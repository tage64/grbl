#!/usr/bin/env python

import argparse
import asyncio
from prompt_toolkit.patch_stdout import patch_stdout

import serial
from prompt_toolkit import PromptSession


async def grbl_repl(port: str) -> None:
    s = serial.Serial(port, 115200)
    # Wake up grbl
    s.write(b"\r\n\r\n")
    s.flush()
    print("Waking up GRBL...")
    await asyncio.sleep(2)  # Wait for grbl to initialize

    exit_event = asyncio.Event()
    prompt_session = PromptSession("grbl> ")

    with patch_stdout():
        await asyncio.gather(
            read_user_input(s, prompt_session, exit_event),
            read_grbl_output(s, exit_event),
        )


async def read_user_input(
    ser_device, prompt_session: PromptSession, exit_event: asyncio.Event
) -> None:
    try:
        while True:
            text = await prompt_session.prompt_async()
            text = text.strip()
            if text == ":exit":
                break
            bytes_ = text.encode("utf-8")
            ser_device.write(bytes_ + b"\n")
            ser_device.flush()
    except EOFError:
        pass
    finally:
        exit_event.set()
    print("Exiting...")


async def read_grbl_output(ser_device, exit_event: asyncio.Event) -> None:
    while not exit_event.is_set():
        await asyncio.sleep(0.01)
        grbl_output = ser_device.read_all()
        if grbl_output:
            text = grbl_output.decode("ascii", errors="replace")
            print(text, end="")
    print("Closing connection to GRBL...")
    ser_device.close()


def main() -> None:
    argparser = argparse.ArgumentParser(
        description="Direct communication with GRBL in a REPL."
    )
    argparser.add_argument("device_file", help="serial device path")
    args = argparser.parse_args()

    asyncio.run(grbl_repl(args.device_file))


if __name__ == "__main__":
    main()
