import argparse
import logging
import traceback

from os import path

import binder_trace.loggers
import binder_trace.constants
import binder_trace.structure
import binder_trace.tui

from binder_trace import loggers
from binder_trace.generator import FridaInjector

loggers.configure()

log = logging.getLogger(loggers.LOG)

def main():
    parser = argparse.ArgumentParser(
        description="Connects to a Android device with a "
        "frida server running and extracts and "
        "parses the data passed across the Binder "
        "interface."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-p", "--pid", dest="pid", type=int, help="the process id to attach to")
    group.add_argument("-n", "--name", dest="name", type=str, help="the process name to attach to")
    
    parser.add_argument("-d", "--device", dest="device", type=str, help="the android device to attach to")

    parser.add_argument(
        "-s", "--structpath", required=True, help="provides the path to the root of the struct directory. e.g. ../structs/android11"
    )

    args = parser.parse_args()

    if args.structpath:
        if not path.exists(args.structpath):
            print("Struct path not found.")
            exit(-1)

    struct_path = args.structpath or "../struct/"
    injector = None
    try:
        injector = FridaInjector(args.pid or args.name, struct_path, binder_trace.constants.ANDROID_VERSION, args.device)
        injector.start()
        binder_trace.tui.start_ui(injector.block_queue)
        log.info("UI Stopped")
    except Exception as err:
        print(err)
        log.error(f"Error occurred in UI: {err}")
        log.error(traceback.format_exc())
    except KeyboardInterrupt:
        pass
    finally:
        if injector:
            injector.stop()
        log.info("Injector stopped.")

if __name__ == "__main__":
    main()
