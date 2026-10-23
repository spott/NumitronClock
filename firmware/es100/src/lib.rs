#![no_std]
//! Full-frame ES100 driver, using the register map in the archived v0.97 datasheet.
//!
//! The application owns EN and IRQ. Raise EN, allow wakeup, then call
//! [`Es100::start_receive`]. One task must timestamp IRQ's falling edge and call
//! [`Es100::irq_status`] exactly once: reading that register acknowledges IRQ.
//! A cycle-complete IRQ is an unsuccessful attempt, not the end of reception.
//! Lower EN on every exit to shut down, including after a bus error or timeout.
//!
//! Every register read is an address write followed by a *separate* read
//! transaction, never a combined (repeated-start) `write_read`. A 2018
//! time-nuts report says the ES100 does not accept the combined form and that
//! the datasheet documents this; the read waveforms on p24 are figures only.

use embedded_hal_async::i2c::I2c;

pub const ADDRESS: u8 = 0x32;
pub const DEVICE_ID: u8 = 0x10;
const CONTROL0: u8 = 0x00;
const IRQ_STATUS: u8 = 0x02;
const STATUS0: u8 = 0x03;
const ID: u8 = 0x0d;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Antenna {
    One,
    Two,
}

/// Full-frame modes only. Tracking requires a separately scheduled protocol.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub enum ReceiveMode {
    #[default]
    AutomaticStartingWithOne,
    AutomaticStartingWithTwo,
    AntennaOneOnly,
    AntennaTwoOnly,
}

impl ReceiveMode {
    fn control(self) -> u8 {
        match self {
            Self::AutomaticStartingWithOne => 0x01,
            Self::AutomaticStartingWithTwo => 0x09,
            Self::AntennaOneOnly => 0x05,
            Self::AntennaTwoOnly => 0x03,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct IrqStatus(pub u8);

impl IrqStatus {
    pub const fn receive_complete(self) -> bool {
        self.0 & 0x01 != 0
    }

    pub const fn cycle_complete(self) -> bool {
        self.0 & 0x04 != 0
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Dst {
    Off,
    EndsToday,
    BeginsToday,
    On,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum LeapSecond {
    None,
    Negative,
    Positive,
}

/// Bits other than RX_OK are meaningful only when RX_OK is set.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Status0(pub u8);

impl Status0 {
    pub const fn rx_ok(self) -> bool {
        self.0 & 1 != 0
    }

    pub const fn tracking(self) -> bool {
        self.0 & 0x80 != 0
    }

    pub const fn antenna(self) -> Antenna {
        if self.0 & 2 == 0 {
            Antenna::One
        } else {
            Antenna::Two
        }
    }

    pub const fn dst(self) -> Dst {
        match (self.0 >> 5) & 3 {
            0 => Dst::Off,
            1 => Dst::EndsToday,
            2 => Dst::BeginsToday,
            _ => Dst::On,
        }
    }

    pub const fn leap_second(self) -> LeapSecond {
        match (self.0 >> 3) & 3 {
            2 => LeapSecond::Negative,
            3 => LeapSecond::Positive,
            _ => LeapSecond::None,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct UtcDateTime {
    /// ES100's two-digit year interpreted as 2000..=2099 (datasheet p19).
    pub year: u16,
    pub month: u8,
    pub day: u8,
    pub hour: u8,
    pub minute: u8,
    /// Preserve a possible leap-second value of 60.
    pub second: u8,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum NextDst {
    /// Hour is **local** time (1..=3 am), not UTC, although datasheet p22
    /// says UTC. Confirmed on hardware 2026-10-23 in Colorado: the ES100
    /// reported 1 Nov, hour 2, and US DST ended Sunday 1 Nov 2026 at 2 am local
    /// (UTC would have been 8).
    Scheduled {
        month: u8,
        day: u8,
        hour: u8,
    },
    /// DSTSpecial says "scheduled", but month/day/hour failed validation.
    /// Raw register values are kept, and the received time is still valid.
    Unrecognized {
        month: u8,
        day: u8,
        hour: u8,
    },
    OutsideSchedule,
    AlwaysOff,
    AlwaysOn,
    Reserved(u8),
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ReceivedTime {
    /// This second starts at IRQ's falling edge, within ES100's timing tolerance.
    /// Do not add a minute or interpret this as the I²C read completion time.
    pub utc: UtcDateTime,
    pub status: Status0,
    pub next_dst: NextDst,
    /// Unmodified registers 0x03..=0x0c for diagnostics.
    pub raw: [u8; 10],
}

#[derive(Debug, Eq, PartialEq)]
pub enum Error<E> {
    I2c(E),
    NotSynchronized,
    TrackingResult,
    InvalidData { register: u8, value: u8 },
}

pub struct Es100<I> {
    i2c: I,
}

impl<I: I2c> Es100<I> {
    pub const fn new(i2c: I) -> Self {
        Self { i2c }
    }

    pub fn free(self) -> I {
        self.i2c
    }

    pub async fn device_id(&mut self) -> Result<u8, Error<I::Error>> {
        self.read_register(ID).await
    }

    /// EN must already be high and wakeup complete. Clears previous results.
    pub async fn start_receive(&mut self, mode: ReceiveMode) -> Result<(), Error<I::Error>> {
        self.i2c
            .write(ADDRESS, &[CONTROL0, mode.control()])
            .await
            .map_err(Error::I2c)
    }

    /// Acknowledges IRQ; call exactly once per observed falling edge.
    pub async fn irq_status(&mut self) -> Result<IrqStatus, Error<I::Error>> {
        self.read_register(IRQ_STATUS).await.map(IrqStatus)
    }

    /// Does not acknowledge IRQ.
    pub async fn status0(&mut self) -> Result<Status0, Error<I::Error>> {
        self.read_register(STATUS0).await.map(Status0)
    }

    /// Read only after a successful full-frame IRQ, before another START.
    /// The burst intentionally starts after IRQ Status, so it cannot acknowledge
    /// another interrupt. ES100 auto-increments register addresses (p23).
    pub async fn read_time(&mut self) -> Result<ReceivedTime, Error<I::Error>> {
        let mut raw = [0; 10];
        self.read_registers(STATUS0, &mut raw).await?;
        decode(raw)
    }

    /// Stop receiving, leaving the chip IDLE. The application must lower EN to
    /// enter SHUTDOWN; do that even if this write fails or times out.
    pub async fn stop(&mut self) -> Result<(), Error<I::Error>> {
        self.i2c
            .write(ADDRESS, &[CONTROL0, 0])
            .await
            .map_err(Error::I2c)
    }

    async fn read_register(&mut self, register: u8) -> Result<u8, Error<I::Error>> {
        let mut value = [0];
        self.read_registers(register, &mut value).await?;
        Ok(value[0])
    }

    /// Address write, then a separate read: see the module documentation.
    async fn read_registers(&mut self, first: u8, out: &mut [u8]) -> Result<(), Error<I::Error>> {
        self.i2c
            .write(ADDRESS, &[first])
            .await
            .map_err(Error::I2c)?;
        self.i2c.read(ADDRESS, out).await.map_err(Error::I2c)
    }
}

fn invalid<E>(register: u8, value: u8) -> Error<E> {
    Error::InvalidData { register, value }
}

fn bcd<E>(register: u8, raw: u8, min: u8, max: u8) -> Result<u8, Error<E>> {
    let lo = raw & 0x0f;
    let hi = raw >> 4;
    let value = hi * 10 + lo;
    if lo > 9 || hi > 9 || value < min || value > max {
        Err(invalid(register, raw))
    } else {
        Ok(value)
    }
}

fn days_in_month(year: u16, month: u8) -> u8 {
    match month {
        2 if year.is_multiple_of(4) => 29, // Supported years are 2000..=2099.
        2 => 28,
        4 | 6 | 9 | 11 => 30,
        _ => 31,
    }
}

fn scheduled_dst(month: u8, day: u8, hour: u8) -> NextDst {
    let parsed = (|| {
        let month = bcd::<()>(0x0a, month, 1, 12).ok()?;
        // Next transition may be in another year: allow Feb 29 here.
        let day = bcd::<()>(0x0b, day, 1, days_in_month(2000, month)).ok()?;
        let hour = bcd::<()>(0x0c, hour, 1, 3).ok()?;
        Some(NextDst::Scheduled { month, day, hour })
    })();
    parsed.unwrap_or(NextDst::Unrecognized { month, day, hour })
}

fn decode<E>(raw: [u8; 10]) -> Result<ReceivedTime, Error<E>> {
    let status = Status0(raw[0]);
    if !status.rx_ok() {
        return Err(Error::NotSynchronized);
    }
    if status.tracking() {
        return Err(Error::TrackingResult);
    }
    let year = 2000 + u16::from(bcd(0x04, raw[1], 0, 99)?);
    let month = bcd(0x05, raw[2], 1, 12)?;
    let day = bcd(0x06, raw[3], 1, days_in_month(year, month))?;
    let utc = UtcDateTime {
        year,
        month,
        day,
        hour: bcd(0x07, raw[4], 0, 23)?,
        minute: bcd(0x08, raw[5], 0, 59)?,
        second: bcd(0x09, raw[6], 0, 60)?,
    };
    let special = raw[9] >> 4;
    let next_dst = match special {
        0..=7 => scheduled_dst(raw[7], raw[8], raw[9] & 0x0f),
        8 => NextDst::OutsideSchedule,
        9 => NextDst::AlwaysOff,
        10 => NextDst::AlwaysOn,
        other => NextDst::Reserved(other),
    };
    Ok(ReceivedTime {
        utc,
        status,
        next_dst,
        raw,
    })
}

#[cfg(test)]
mod tests;
