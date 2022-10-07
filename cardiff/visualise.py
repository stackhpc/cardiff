from pyvis.network import Network


class Visualiser():
    fields = {
        "HPA Controller": ('#be1313', 0.1, 'curvedCW'),
        "HPA Disks": ("#f17474", 0.2, 'curvedCW'),
        "Megaraid Controller": ("#b59412", 0.3, 'curvedCW'),
        "Megaraid Disks": ("#f8f254", 0.4, 'curvedCW'),
        "AHCI Controller": ("#e67c0a", 0.5, 'curvedCW'),
        "System": ("#08c908", 0.1, 'curvedCCW'),
        "Firmware": ("#08b2c9", 0.2, 'curvedCCW'),
        "DDR Timing": ("#083fc9", 0.3, 'curvedCCW'),
        "Network Interfaces": ("#9208c9", 0.4, 'curvedCCW'),
        "Processors": ("#f74abe", 0.5, 'curvedCCW')
    }

    class Group():
        id = 0
        title = ""
        serials = []
        connections = {}

        def __init__(self, id, title, serials):
            self.id = id
            self.title = title
            self.serials = serials
            self.connections = {}

        def add_connection(self, label, target, dataless):
            if label not in self.connections:
                self.connections[label] = (set(), dataless)
                self.connections[label][0].add(target)
            else:
                self.connections[label][0].add(target)

    results = {}
    performance_stats = {}
    groups = []
    output_dir = ""
    shared_fields = set()
    dataless_fields = set()
    names_dict = {}

    def __init__(self, output_dir, names_dict):
        self.output_dir = output_dir
        self.names_dict = names_dict

    def add_result(self, title, result):
        self.results[title] = result

    def print_results(self, file):
        for item in self.results:
            print(item, self.results[item], file=file)

    def add_group(self, id, title, serials):
        group = Visualiser.Group(id, title, serials)
        self.groups.append(group)

    def compare_serials(self, group, other_group, systems, label, dataless):
        if (group.id != other_group.id
                and other_group.serials[0] not in systems):
            if label in self.shared_fields:
                self.shared_fields.remove(label)
            if label not in other_group.connections:
                if group.id < other_group.id:
                    group.add_connection(
                        label, other_group.id, dataless)
                else:
                    other_group.add_connection(
                        label, group.id, dataless)
            elif group.id not in other_group.connections[label][0]:
                if group.id < other_group.id:
                    group.add_connection(
                        label, other_group.id, dataless)
                else:
                    other_group.add_connection(
                        label, group.id, dataless)

    def extract_connections(self):
        for item in self.results:
            label = item
            for group in self.groups:
                for element in self.results[item]:
                    if eval(element) == set():
                        dataless = True
                        self.dataless_fields.add(label)
                    else:
                        dataless = False
                        self.shared_fields.add(label)
                    systems = self.results[item][element]
                    if group.serials[0] in systems:
                        for other_group in self.groups:
                            self.compare_serials(group, other_group, systems,
                                                 label, dataless)

    def print_connections(self, file):
        for group in self.groups:
            print(group.title, group.connections, file=file)

    def differences_network(self):
        net = Network(directed=True, width="1600px", height="900px")

        self.extract_connections()

        label_unique = ("Hover over a group to see the systems it contains.\n"
                        "Edges represent differing fields.\n\n"
                        "Fully shared fields:\n- ") + \
            "\n- ".join(self.shared_fields) + \
            "\n\nDataless fields:\n- " + \
            "\n- ".join(self.dataless_fields)
        net.add_node(
            n_id=-1,
            label=label_unique,
            color='grey',
            value=len(self.shared_fields),
            x=0,
            y=0,
            shape='text')

        for group in self.groups:
            names = []
            for serial in group.serials:
                names.append("%s - %s" % (self.names_dict[serial], serial))
            net.add_node(
                n_id=group.id,
                label=group.title,
                title="\n".join(names),
                color='grey',
                value=len(group.serials))

        for group in self.groups:
            for connection in group.connections:
                info = group.connections[connection]
                if (info[1] == False):
                    count = 0
                    width = 1.5
                    font_size = 9
                    if group.connections[connection][1]:
                        width = 0.3
                        font_size = 5
                    for target in info[0]:
                        net.add_edge(
                            source=group.id,
                            to=target,
                            width=width,
                            label=connection,
                            color=self.fields[connection][0],
                            smooth={
                                'type': self.fields[connection][2],
                                'roundness': self.fields[connection][1]},
                            font={'size': font_size, 'align': 'middle'},
                            arrows={'to': {'enabled': False}},
                            dashes=group.connections[connection][1],
                            hoverWidth=0.05)
                        count += 1

        net.toggle_physics(False)
        try:
            net.show("%s/_result.html" % self.output_dir)
        except Exception as e:
            print(e)

    def visualise(self):
        self.differences_network()
