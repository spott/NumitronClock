#![no_std]
#![no_main]

use core::future::Future;
use embassy_executor::Spawner;
use embassy_rp::{
    bind_interrupts,
    gpio::{Input, Level, Output, Pull},
    i2c::{self, Async, I2c},
    peripherals::{I2C0, USB},
    usb::{self, Driver},
};
use embassy_time::{Duration, Instant, Timer, with_deadline, with_timeout};
use es100::{Es100, ReceiveMode, ReceivedTime};
use panic_halt as _;

type Receiver = Es100<I2c<'static, I2C0, Async>>;
const RECEIVE_TIMEOUT: Duration = Duration::from_secs(20 * 60);
const BUS_TIMEOUT: Duration = Duration::from_secs(3);
const RETRY_DELAY: Duration = Duration::from_secs(30);
const MODE: ReceiveMode = ReceiveMode::AutomaticStartingWithOne;
/// Wait between the IRQ edge timestamp and the first IRQ Status read. A 2018
/// time-nuts report says reading right at the edge returns stale zeros and "a
/// small read delay is needed", without a figure. Tune on the bench.
const IRQ_STATUS_DELAY: Duration = Duration::from_millis(10);
/// If IRQ Status still reads 0 while IRQ is low, nothing was acknowledged:
/// wait and read again, up to this many reads in total.
const IRQ_STATUS_READS: u32 = 10;
/// After an acknowledged cycle-complete, IRQ must return high within this.
const IRQ_RELEASE_TIMEOUT: Duration = Duration::from_millis(100);
/// Stop retrying after this many consecutive failed attempts (not timeouts).
const MAX_CONSECUTIVE_ERRORS: u32 = 5;

bind_interrupts!(struct Irqs {
    USBCTRL_IRQ => usb::InterruptHandler<USB>;
    I2C0_IRQ => i2c::InterruptHandler<I2C0>;
});

#[embassy_executor::task]
async fn usb_logger(driver: Driver<'static, USB>) {
    // This logger version handles USB disconnect/reconnect without panicking.
    // Writes use a bounded, nonblocking buffer: reception never waits for a PC.
    embassy_usb_logger::run!(8192, log::LevelFilter::Info, driver);
}

#[derive(Debug)]
enum AttemptError {
    Bus(es100::Error<i2c::Error>),
    BusTimeout,
    WrongDeviceId(u8),
    IrqStuckLow,
    UnexpectedIrq(u8),
    ReceiveTimeout,
}

async fn bus<T>(
    operation: impl Future<Output = Result<T, es100::Error<i2c::Error>>>,
) -> Result<T, AttemptError> {
    with_timeout(BUS_TIMEOUT, operation)
        .await
        .map_err(|_| AttemptError::BusTimeout)?
        .map_err(AttemptError::Bus)
}

/// Single owner of IRQ Status. No diagnostic task reads/acknowledges it.
async fn receive(receiver: &mut Receiver, irq: &mut Input<'static>) -> Result<(), AttemptError> {
    let id = bus(receiver.device_id()).await?;
    log::info!("device_id=0x{:02x} expected=0x{:02x}", id, es100::DEVICE_ID);
    if id != es100::DEVICE_ID {
        return Err(AttemptError::WrongDeviceId(id));
    }
    if irq.is_low() {
        return Err(AttemptError::IrqStuckLow);
    }
    let started = Instant::now();
    let deadline = started + RECEIVE_TIMEOUT;
    bus(receiver.start_receive(MODE)).await?;
    log::info!(
        "receive_start monotonic_us={} mode={:?}",
        started.as_micros(),
        MODE
    );
    let mut cycles = 0u32;
    loop {
        with_deadline(deadline, irq.wait_for_falling_edge())
            .await
            .map_err(|_| AttemptError::ReceiveTimeout)?;
        let edge = Instant::now(); // Take before any bus transaction or logging.
        let (status, reads) = read_irq_status(receiver, irq).await?;
        cycles += 1;
        let elapsed_ms = (edge - started).as_millis();
        log::info!(
            "irq edge_us={} elapsed_ms={} cycle={} irq_status=0x{:02x} status_reads={}",
            edge.as_micros(),
            elapsed_ms,
            cycles,
            status.0,
            reads
        );
        // Prefer a successful result if both flags happen to be present.
        if status.receive_complete() {
            let time = bus(receiver.read_time()).await?;
            log_time(time, edge, elapsed_ms, cycles);
            return Ok(());
        }
        if status.cycle_complete() {
            log::info!("cycle_complete: unsuccessful; ES100 continues receiving");
            // The read acknowledged IRQ, so it should already be high again.
            // If it is not, the next falling edge could never be observed.
            with_timeout(IRQ_RELEASE_TIMEOUT, irq.wait_for_high())
                .await
                .map_err(|_| AttemptError::IrqStuckLow)?;
            // Do not issue another START: it clears the previous result and
            // defeats the ES100's automatic alternating-antenna receive cycle.
            continue;
        }
        return Err(AttemptError::UnexpectedIrq(status.0));
    }
}

/// The single owner of IRQ Status reads. A nonzero value acknowledges IRQ, so
/// it is read once. A zero while IRQ is still low is the stale value seen when
/// reading too early; nothing was acknowledged, so wait and read again.
async fn read_irq_status(
    receiver: &mut Receiver,
    irq: &mut Input<'static>,
) -> Result<(es100::IrqStatus, u32), AttemptError> {
    let mut reads = 0;
    loop {
        Timer::after(IRQ_STATUS_DELAY).await;
        let status = bus(receiver.irq_status()).await?;
        reads += 1;
        if status.0 != 0 || irq.is_high() || reads >= IRQ_STATUS_READS {
            return Ok((status, reads));
        }
    }
}

fn log_time(time: ReceivedTime, edge: Instant, elapsed_ms: u64, cycles: u32) {
    let utc = time.utc;
    log::info!(
        "lock utc={:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z edge_us={} elapsed_ms={} cycles={}",
        utc.year,
        utc.month,
        utc.day,
        utc.hour,
        utc.minute,
        utc.second,
        edge.as_micros(),
        elapsed_ms,
        cycles
    );
    log::info!(
        "status0=0x{:02x} antenna={:?} dst={:?} leap={:?} next_dst={:?} raw={:02x?}",
        time.status.0,
        time.status.antenna(),
        time.status.dst(),
        time.status.leap_second(),
        time.next_dst,
        time.raw
    );
}

fn log_error(error: &AttemptError) {
    match error {
        AttemptError::Bus(cause) => log::error!("bus/result error: {:?}", cause),
        AttemptError::WrongDeviceId(id) => log::error!("wrong ES100 device ID: 0x{:02x}", id),
        AttemptError::UnexpectedIrq(raw) => log::error!("unexpected IRQ Status: 0x{:02x}", raw),
        other => log::error!("receive error: {:?}", other),
    }
}

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    let p = embassy_rp::init(Default::default());
    let mut en = Output::new(p.PIN_2, Level::Low);
    let mut irq = Input::new(p.PIN_3, Pull::None); // External pull-up, including in shutdown.
    let mut led = Output::new(p.PIN_25, Level::Low);
    let mut config = i2c::Config::default();
    config.frequency = 100_000;
    config.sda_pullup = false; // Fit external pull-ups if absent from carrier.
    config.scl_pullup = false;
    let i2c = I2c::new_async(p.I2C0, p.PIN_5, p.PIN_4, Irqs, config);
    let mut receiver = Es100::new(i2c);
    let usb = Driver::new(p.USB, Irqs);
    spawner.spawn(usb_logger(usb)).unwrap();
    Timer::after_secs(3).await; // Allow enumeration; receive does not require a terminal.
    log::info!("ES100 Pico 2 test firmware {}", env!("CARGO_PKG_VERSION"));
    log::info!(
        "EN=GP2 IRQ=GP3 SDA=GP4 SCL=GP5; deadline=1200s retry=30s irq_status_delay_ms={} max_consecutive_errors={}",
        IRQ_STATUS_DELAY.as_millis(),
        MAX_CONSECUTIVE_ERRORS
    );
    log::info!("edge_us is a software observation after GPIO wake, not a hardware capture");
    let mut attempt = 0u32;
    let mut consecutive_errors = 0u32;
    loop {
        attempt += 1;
        log::info!(
            "attempt={} begin; EN=low irq_high={}",
            attempt,
            irq.is_high()
        );
        en.set_high();
        Timer::after_millis(100).await; // Conservative module/crystal startup; IC minimum 1 ms.
        led.set_high();
        let result = receive(&mut receiver, &mut irq).await;
        // EN shuts down directly (datasheet p7-p9). Never issue more bus I/O
        // after a possibly cancelled transfer. Successful full-frame reception
        // already clears START; a timeout is terminated by this falling EN.
        en.set_low();
        led.set_low();
        let mut fatal = None;
        match result {
            Ok(()) => {
                consecutive_errors = 0;
                log::info!("attempt={} result=lock", attempt);
            }
            Err(AttemptError::ReceiveTimeout) => {
                consecutive_errors = 0;
                log::warn!("attempt={} result=timeout budget_s=1200", attempt);
            }
            Err(AttemptError::BusTimeout) => {
                log_error(&AttemptError::BusTimeout);
                // Do not reuse an I2C peripheral after cancelling a stuck transfer.
                fatal = Some("I2C transfer timed out; peripheral not reused");
            }
            Err(ref error) => {
                // Completed I2C errors (NACK etc.) leave the peripheral usable:
                // shut down, rest and retry.
                consecutive_errors += 1;
                log_error(error);
                log::warn!(
                    "attempt={} result=error consecutive_errors={}/{}",
                    attempt,
                    consecutive_errors,
                    MAX_CONSECUTIVE_ERRORS
                );
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS {
                    fatal = Some("too many consecutive errors");
                }
            }
        }
        if let Some(reason) = fatal {
            // Keep USB diagnostics alive with the radio shut down until reset.
            loop {
                log::error!(
                    "stopped: {}. EN=low: check wiring/pull-ups and reset the Pico; see prior error",
                    reason
                );
                led.set_high();
                Timer::after_millis(100).await;
                led.set_low();
                Timer::after_secs(5).await;
            }
        }
        log::info!("attempt={} end; EN=low retry_in_s=30", attempt);
        Timer::after(RETRY_DELAY).await;
    }
}
