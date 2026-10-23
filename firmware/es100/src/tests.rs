extern crate std;

use super::*;
use embedded_hal_async::i2c::{ErrorKind, ErrorType, Operation};
use futures::executor::block_on;
use std::{collections::VecDeque, vec, vec::Vec};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct BusError;
impl embedded_hal_async::i2c::Error for BusError {
    fn kind(&self) -> ErrorKind {
        ErrorKind::Other
    }
}

enum Step {
    Write(Vec<u8>),
    Read(u8, Vec<u8>),
    Fail,
}
struct Bus(VecDeque<Step>);
impl ErrorType for Bus {
    type Error = BusError;
}
impl I2c for Bus {
    async fn transaction(
        &mut self,
        address: u8,
        ops: &mut [Operation<'_>],
    ) -> Result<(), BusError> {
        assert_eq!(address, 0x32, "7-bit address, not shifted wire address");
        match (self.0.pop_front().expect("unexpected I2C access"), ops) {
            (Step::Write(expected), [Operation::Write(actual)]) => assert_eq!(*actual, expected),
            (Step::Read(register, data), [Operation::Write(actual), Operation::Read(out)]) => {
                assert_eq!(*actual, [register]);
                assert_eq!(out.len(), data.len());
                out.copy_from_slice(&data);
            }
            (Step::Fail, _) => return Err(BusError),
            _ => panic!("unexpected I2C transaction shape"),
        }
        Ok(())
    }
}
fn bus(steps: Vec<Step>) -> Bus {
    Bus(steps.into())
}
fn done(driver: Es100<Bus>) {
    assert!(driver.free().0.is_empty(), "missing transaction");
}

// Datasheet p19-p22 encodings: 2049-11-26 23:57:48; next DST Nov 3, hour 2.
const FRAME: [u8; 10] = [0x63, 0x49, 0x11, 0x26, 0x23, 0x57, 0x48, 0x11, 0x03, 0x02];

#[test]
fn device_id_and_all_documented_full_frame_modes() {
    block_on(async {
        let mut driver = Es100::new(bus(vec![
            Step::Read(0x0d, vec![0x10]),
            Step::Write(vec![0, 1]),
            Step::Write(vec![0, 9]),
            Step::Write(vec![0, 5]),
            Step::Write(vec![0, 3]),
            Step::Write(vec![0, 0]),
        ]));
        assert_eq!(driver.device_id().await, Ok(DEVICE_ID));
        for mode in [
            ReceiveMode::AutomaticStartingWithOne,
            ReceiveMode::AutomaticStartingWithTwo,
            ReceiveMode::AntennaOneOnly,
            ReceiveMode::AntennaTwoOnly,
        ] {
            driver.start_receive(mode).await.unwrap();
        }
        driver.stop().await.unwrap();
        done(driver);
    });
}

#[test]
fn unsuccessful_cycle_then_success_does_not_require_a_new_start_or_extra_ack() {
    block_on(async {
        let mut driver = Es100::new(bus(vec![
            Step::Write(vec![0, 1]),
            Step::Read(2, vec![4]),
            Step::Read(2, vec![1]),
            Step::Read(3, FRAME.to_vec()),
        ]));
        driver.start_receive(ReceiveMode::default()).await.unwrap();
        let cycle = driver.irq_status().await.unwrap();
        assert!(cycle.cycle_complete());
        assert!(!cycle.receive_complete());
        let success = driver.irq_status().await.unwrap();
        assert!(success.receive_complete());
        assert!(!success.cycle_complete());
        let result = driver.read_time().await.unwrap();
        assert_eq!(
            result.utc,
            UtcDateTime {
                year: 2049,
                month: 11,
                day: 26,
                hour: 23,
                minute: 57,
                second: 48,
            }
        );
        assert_eq!(result.status.antenna(), Antenna::Two);
        assert_eq!(result.status.dst(), Dst::On);
        assert_eq!(
            result.next_dst,
            NextDst::Scheduled {
                month: 11,
                day: 3,
                hour: 2
            }
        );
        assert_eq!(result.raw, FRAME);
        done(driver);
    });
}

#[test]
fn status_read_never_acknowledges_irq() {
    block_on(async {
        let mut driver = Es100::new(bus(vec![Step::Read(3, vec![0x83])]));
        let status = driver.status0().await.unwrap();
        assert!(status.rx_ok());
        assert!(status.tracking());
        assert_eq!(status.antenna(), Antenna::Two);
        done(driver);
    });
}

#[test]
fn dst_and_leap_encodings_match_the_datasheet_tables() {
    for (raw, dst) in [
        (0x01, Dst::Off),
        (0x21, Dst::EndsToday),
        (0x41, Dst::BeginsToday),
        (0x61, Dst::On),
    ] {
        assert_eq!(Status0(raw).dst(), dst);
    }
    for (raw, leap) in [
        (0x01, LeapSecond::None),
        (0x09, LeapSecond::None),
        (0x11, LeapSecond::Negative),
        (0x19, LeapSecond::Positive),
    ] {
        assert_eq!(Status0(raw).leap_second(), leap);
    }
}

#[test]
fn invalid_or_tracking_frames_never_become_a_date() {
    for (status, error) in [(0, Error::NotSynchronized), (0x81, Error::TrackingResult)] {
        let mut raw = FRAME;
        raw[0] = status;
        assert_eq!(decode::<BusError>(raw), Err(error));
    }
}

#[test]
fn rejects_malformed_bcd_and_calendar_ranges() {
    for (index, value) in [
        (1, 0xfa),
        (2, 0),
        (2, 0x13),
        (3, 0),
        (3, 0x32),
        (4, 0x24),
        (5, 0x60),
        (5, 0x1a),
        (6, 0x61),
        (7, 0x13),
        (8, 0x32),
        (9, 0x04),
    ] {
        let mut raw = FRAME;
        raw[index] = value;
        assert_eq!(
            decode::<BusError>(raw),
            Err(Error::InvalidData {
                register: 3 + index as u8,
                value,
            })
        );
    }
    let mut raw = FRAME;
    raw[2] = 0x02;
    raw[3] = 0x29;
    assert!(decode::<BusError>(raw).is_err()); // 2049 is not a leap year.
    raw[1] = 0x00;
    assert!(decode::<BusError>(raw).is_ok()); // 2000 is a leap year.
    raw[2] = 0x04;
    raw[3] = 0x31;
    assert!(decode::<BusError>(raw).is_err());
}

#[test]
fn next_dst_special_values_do_not_validate_invalid_date_registers() {
    for (nibble, expected) in [
        (8, NextDst::OutsideSchedule),
        (9, NextDst::AlwaysOff),
        (10, NextDst::AlwaysOn),
        (15, NextDst::Reserved(15)),
    ] {
        let mut raw = FRAME;
        raw[7] = 0xff;
        raw[8] = 0xff;
        raw[9] = nibble << 4;
        assert_eq!(decode::<BusError>(raw).unwrap().next_dst, expected);
    }
}

#[test]
fn midnight_and_leap_second_are_preserved_without_arithmetic() {
    let mut raw = FRAME;
    raw[1..7].copy_from_slice(&[0x26, 0x12, 0x31, 0, 0, 0]);
    let time = decode::<BusError>(raw).unwrap().utc;
    assert_eq!((time.hour, time.minute, time.second), (0, 0, 0));
    raw[4..7].copy_from_slice(&[0x23, 0x59, 0x60]);
    assert_eq!(decode::<BusError>(raw).unwrap().utc.second, 60);
}

#[test]
fn bus_errors_propagate_from_every_operation() {
    block_on(async {
        let mut driver = Es100::new(bus((0..6).map(|_| Step::Fail).collect()));
        assert_eq!(driver.device_id().await, Err(Error::I2c(BusError)));
        assert_eq!(
            driver.start_receive(ReceiveMode::default()).await,
            Err(Error::I2c(BusError))
        );
        assert_eq!(driver.irq_status().await, Err(Error::I2c(BusError)));
        assert_eq!(driver.status0().await, Err(Error::I2c(BusError)));
        assert_eq!(driver.read_time().await, Err(Error::I2c(BusError)));
        assert_eq!(driver.stop().await, Err(Error::I2c(BusError)));
        done(driver);
    });
}
