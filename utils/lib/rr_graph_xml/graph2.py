""" Graph object that handles serialization and deserialization from XML. """
from lib.rr_graph import graph2
from lib.rr_graph import tracks
import copy
import lxml.etree as ET
import contextlib

def enum_from_string(enum_type, s):
    for e in enum_type:
        if e.name == s.upper():
            return e

    assert False, (enum_type, s)

def graph_from_xml(input_xml, progressbar=None):
    if progressbar is None:
        progressbar = lambda x: x

    switches = []
    for switch in input_xml.find('switches').iter('switch'):
        timing_xml = switch.find('timing')

        if timing_xml is not None:
            timing = graph2.SwitchTiming(
                    r=float(timing_xml.attrib['R']),
                    c_in=float(timing_xml.attrib['Cin']),
                    c_out=float(timing_xml.attrib['Cout']),
                    t_del=float(timing_xml.attrib['Tdel']),
            )
        else:
            timing = None

        sizing_xml = switch.find('sizing')

        if sizing_xml is not None:
            sizing = graph2.SwitchSizing(
                    mux_trans_size=float(sizing_xml.attrib['mux_trans_size']),
                    buf_size=float(sizing_xml.attrib['buf_size']),
            )
        else:
            sizing = None

        switches.append(graph2.Switch(
                id=int(switch.attrib['id']),
                type=enum_from_string(graph2.SwitchType, switch.attrib['type']),
                name=switch.attrib['name'],
                timing=timing,
                sizing=sizing,
        ))

    segments = []
    for segment in input_xml.find('segments').iter('segment'):
        timing_xml = segment.find('timing')

        if timing_xml is not None:
            timing = graph2.SegmentTiming(
                    r_per_meter=float(timing_xml.attrib['R_per_meter']),
                    c_per_meter=float(timing_xml.attrib['C_per_meter']),
            )
        else:
            timing = None

        segments.append(graph2.Segment(
                id=int(segment.attrib['id']),
                name=segment.attrib['name'],
                timing=timing,
        ))

    block_types = []
    for block_type in input_xml.find('block_types').iter('block_type'):
        pin_classes = []

        for pin_class in block_type.iter('pin_class'):
            pins = []
            for pin in pin_class.iter('pin'):
                pins.append(graph2.Pin(
                        ptc=int(pin.attrib['ptc']),
                        name=pin.text,
                ))

            pin_classes.append(graph2.PinClass(
                    type=enum_from_string(graph2.PinType, pin_class.attrib['type']),
                    pin=pins,
            ))

        block_types.append(graph2.BlockType(
                id=int(block_type.attrib['id']),
                name=block_type.attrib['name'],
                width=int(block_type.attrib['width']),
                height=int(block_type.attrib['height']),
                pin_class=pin_classes,
        ))

    grid = []
    for grid_loc in input_xml.find('grid').iter('grid_loc'):
        grid.append(graph2.GridLoc(
                x=int(grid_loc.attrib['x']),
                y=int(grid_loc.attrib['y']),
                block_type_id=int(grid_loc.attrib['block_type_id']),
                width_offset=int(grid_loc.attrib['width_offset']),
                height_offset=int(grid_loc.attrib['height_offset']),
        ))

    nodes = []
    for node in progressbar(input_xml.find('rr_nodes').iter('node')):
        node_type = enum_from_string(graph2.NodeType, node.attrib['type'])
        if node_type in [graph2.NodeType.SOURCE, graph2.NodeType.SINK,
                            graph2.NodeType.OPIN, graph2.NodeType.IPIN]:

            loc_xml = node.find('loc')
            if loc_xml is not None:
                if 'side' in loc_xml.attrib:
                    side = enum_from_string(tracks.Direction, loc_xml.attrib['side'])
                else:
                    side = None

                loc = graph2.NodeLoc(
                        x_low=int(loc_xml.attrib['xlow']),
                        y_low=int(loc_xml.attrib['ylow']),
                        x_high=int(loc_xml.attrib['xhigh']),
                        y_high=int(loc_xml.attrib['yhigh']),
                        ptc=int(loc_xml.attrib['ptc']),
                        side=side
                )
            else:
                loc = None

            timing_xml = node.find('timing')
            if timing_xml is not None:
                timing = graph2.NodeTiming(
                        r=float(timing_xml.attrib['R']),
                        c=float(timing_xml.attrib['C']),
                )
            else:
                timing = None

            # Not expecting any metadata on the input.
            assert node.find('metadata') is None
            metadata = None
            nodes.append(graph2.Node(
                    id=int(node.attrib['id']),
                    type=node_type,
                    direction=graph2.NodeDirection.NO_DIR,
                    capacity=int(node.attrib['capacity']),
                    loc=loc,
                    timing=timing,
                    metadata=metadata,
                    segment=None,
            ))

    return dict(
            switches=switches,
            segments=segments,
            block_types=block_types,
            grid=grid,
            nodes=nodes
    )

def AddNodeMetadata(root, metadata):
    metadata_xml = ET.SubElement(root, 'metadata')
    for m in metadata:
        ET.SubElement(metadata_xml, 'meta', {
                'name': m.name,
                'x_offset': str(m.x_offset),
                'y_offset': str(m.y_offset),
                'z_offset': str(m.z_offset),
        }).text = m.value

class Graph(object):
    def __init__(self, input_xml, output_file_name=None, progressbar=None):
        if progressbar is None:
            self.progressbar = lambda x: x

        self.input_xml = input_xml
        self.progressbar = progressbar
        self.output_file_name = output_file_name

        graph_input = graph_from_xml(input_xml, progressbar)

        rebase_nodes = []
        for node in progressbar(graph_input['nodes']):
            node_d = node._asdict()
            node_d['id'] = len(rebase_nodes)
            rebase_nodes.append(graph2.Node(**node_d))

        graph_input['nodes'] = rebase_nodes

        self.graph = graph2.Graph(**graph_input)

        self.exit_stack = None
        self.xf = None

    def __enter__(self):
        assert self.output_file_name is not None
        assert self.exit_stack is None
        self.exit_stack = contextlib.ExitStack().__enter__()

        f = self.exit_stack.enter_context(open(self.output_file_name, 'wb'))
        self.xf = self.exit_stack.enter_context(ET.xmlfile(f))

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        ret = self.exit_stack.__exit__(exc_type, exc_value, traceback)
        self.exit_stack = None
        self.xf = None
        return ret

    def start_serialize_to_xml(self, tool_version, tool_comment, channels_obj):
        assert self.exit_stack is not None
        assert self.xf is not None

        self.exit_stack.enter_context(self.xf.element('rr_graph', {
                'tool_name': 'vpr',
                'tool_version': tool_version,
                'tool_comment': tool_comment,
        }))

        self.graph.check_ptc()

        with self.xf.element('channels'):
            el = ET.Element('channel', {
                    'chan_width_max': str(channels_obj.chan_width_max),
                    'x_min': str(channels_obj.x_min),
                    'y_min': str(channels_obj.y_min),
                    'x_max': str(channels_obj.x_max),
                    'y_max': str(channels_obj.y_max),
            })
            self.xf.write(el)

            for x_list in channels_obj.x_list:
                el = ET.Element('x_list', {
                    'index': str(x_list.index),
                    'info': str(x_list.info),
                })
                self.xf.write(el)

            for y_list in channels_obj.y_list:
                el = ET.Element('y_list', {
                    'index': str(y_list.index),
                    'info': str(y_list.info),
                })
                self.xf.write(el)

        self.xf.write(self.input_xml.find('switches'))
        self.xf.write(self.input_xml.find('segments'))
        self.xf.write(self.input_xml.find('block_types'))
        self.xf.write(self.input_xml.find('grid'))

    def serialize_nodes(self, nodes):
        with self.xf.element('rr_nodes'):
            for node in nodes:
                attrib = {
                        'id': str(node.id),
                        'type': node.type.name,
                        'capacity': str(node.capacity),
                        }

                if node.direction != graph2.NodeDirection.NO_DIR:
                    attrib['direction'] = node.direction.name

                with self.xf.element('node', attrib):
                    if node.loc is not None:
                        loc = {
                                'xlow': str(node.loc.x_low),
                                'ylow': str(node.loc.y_low),
                                'xhigh': str(node.loc.x_high),
                                'yhigh': str(node.loc.y_high),
                                'ptc': str(node.loc.ptc),
                        }

                    if node.loc.side is not None:
                        loc['side'] = node.loc.side.name

                    el = ET.Element('loc', loc)
                    self.xf.write(el)

                    if node.timing is not None:
                        el = ET.Element('timing', {
                                'R': str(node.timing.r),
                                'C': str(node.timing.c),
                        })
                        self.xf.write(el)

                    if node.metadata is not None and len(node.metadata) > 0:
                        with self.xf.element('metadata'):
                            for m in node.metadata:
                                el = ET.Element('meta', {
                                        'name': m.name,
                                        'x_offset': str(m.x_offset),
                                        'y_offset': str(m.y_offset),
                                        'z_offset': str(m.z_offset),
                                })
                                el.text = m.value
                                self.xf.write(el)

                    if node.segment is not None:
                        el = ET.Element('segment', {
                                'segment_id': str(node.segment.segment_id),
                        })

                        self.xf.write(el)

    def serialize_edges(self, edges):
        with self.xf.element('rr_edges'):
            for edge in edges:
                edge_xml = ET.Element('edge', {
                        'src_node': str(edge.src_node),
                        'sink_node': str(edge.sink_node),
                        'switch_id': str(edge.switch_id),
                })

                if edge.metadata is not None:
                    AddNodeMetadata(edge_xml, edge.metadata)

                self.xf.write(edge_xml)

    def serialize_to_xml(self, tool_version, tool_comment, pad_segment, channels_obj=None, pool=None):
        if channels_obj is None:
            channels_obj = self.graph.create_channels(
                    pad_segment=pad_segment,
                    pool=pool,
            )

        with self:
            self.start_serialize_to_xml(
                    tool_version=tool_version,
                    tool_comment=tool_comment,
                    channels_obj=channels_obj,
                    )
            self.serialize_nodes(self.progressbar(self.graph.nodes))
            self.serialize_edges(self.progressbar(self.graph.edges))
