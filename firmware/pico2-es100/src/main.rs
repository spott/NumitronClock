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
        if irq.is_low() {
            // There is no observed falling edge to timestamp. Reset this run
            // rather than quietly labelling a late sample as an edge.
            return Err(AttemptError::IrqStuckLow);
        }
        with_deadline(deadline, irq.wait_for_falling_edge())
            .await
            .map_err(|_| AttemptError::ReceiveTimeout)?;
        let edge = Instant::now(); // Take before any bus transaction or logging.
        let status = bus(receiver.irq_status()).await?; // ACK exactly once.
        cycles += 1;
        let elapsed_ms = (edge - started).as_millis();
        log::info!(
            "irq edge_us={} elapsed_ms={} cycle={} irq_status=0x{:02x}",
            edge.as_micros(),
            elapsed_ms,
            cycles,
            status.0
        );
        // Prefer a successful result if both flags happen to be present.
        if status.receive_complete() {
            let time = bus(receiver.read_time()).await?;
            log_time(time, edge, elapsed_ms, cycles);
            return Ok(());
        }
        if status.cycle_complete() {
            log::info!("cycle_complete: unsuccessful; ES100 continues receiving");
            // Do not issue another START: it clears the previous result and
            // defeats the ES100's automatic alternating-antenna receive cycle.
            continue;
        }
        return Err(AttemptError::UnexpectedIrq(status.0));
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
    log::info!("EN=GP2 IRQ=GP3 SDA=GP4 SCL=GP5; deadline=1200s retry=30s");
    log::info!("edge_us is a software observation after GPIO wake, not a hardware capture");
    let mut attempt = 0u32;
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
        let mut fatal = false;
        match result {
            Ok(()) => log::info!("attempt={} result=lock", attempt),
            Err(AttemptError::ReceiveTimeout) => {
                log::warn!("attempt={} result=timeout budget_s=1200", attempt);
            }
            Err(ref error) => {
                log_error(error);
                fatal = true;
            }
        }
        if fatal {
            // Do not reuse an I2C peripheral after cancelling a stuck transfer.
            // Keep USB diagnostics alive with the radio shut down until reset.
            loop {
                log::error!("EN=low: check wiring/pull-ups and reset the Pico; see prior error");
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
