import json
import argparse
import os, shutil
import otf2
import time

def convertTrace(input, output):
    if not input:
      raise Exception("No chrome trace found")

    process_map = {}
    function_map = {}

    with open(input) as json_file:
        chrome_data = json.load(json_file)
        with otf2.writer.open(output, timer_resolution=TIMER_GRANULARITY) as otf2_trace: # TODO definitions=trace_reader.definitions
            otf2_root_node = otf2_trace.definitions.system_tree_node("root node")
            otf2_system_tree_node = otf2_trace.definitions.system_tree_node("myHost", parent=otf2_root_node)
            otf2_location_group = otf2_trace.definitions.location_group("Master Process",
                                                                        system_tree_parent=otf2_system_tree_node)

            for chrome_event in chrome_data['traceEvents']:
                if chrome_event['ph'] == 'M' and chrome_event['name'] == 'process_name':
                    otf2_thread = otf2_trace.event_writer("Main Thread", group=otf2_location_group)
                    process_map[chrome_event['pid']] = otf2_thread

                if chrome_event['ph'] == 'X' and chrome_event['cat'] == "Op":
                    if not chrome_event['name'] in function_map:
                        otf2_function = otf2_trace.definitions.region(chrome_event['name'])
                        function_map[chrome_event['name']] = otf2_function

                    otf2_thread = process_map[chrome_event['pid']]
                    begin = chrome_event['ts']
                    end = begin + chrome_event['dur']
                    function = function_map[chrome_event['name']]
                    otf2_thread.enter(begin, function)
                    otf2_thread.leave(end, function)




def main():
    parser = argparse.ArgumentParser(description="Convert chrome traces into OTF2")
    parser.add_argument(
        "-i", "--input",
        type=str, required=True,
        help="chrome tracing file",
    )
    parser.add_argument(
        "-o", "--output",
        type=str, required=True,
        help="OTF2 Tracing folder",
    )
    parser.add_argument(
        "-c", "--clean",
        action = "store_true",
        help="Clean (delete) the output folder if it exists",
    )
    args = parser.parse_args()

    out_folder = args.output
    if args.clean and os.path.exists(out_folder):
        shutil.rmtree(out_folder)

    convertTrace(args.input, out_folder)
