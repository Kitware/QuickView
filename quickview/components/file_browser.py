import json
import re
from pathlib import Path
from paraview import simple
from trame.widgets import vuetify3 as v3, html
from trame.app import TrameComponent

DIRECTORY = dict(icon="mdi-folder", type="directory")
GROUP = dict(icon="mdi-file-document-multiple-outline", type="group")
FILE = dict(icon="mdi-file-document-outline", type="file")

HEADERS = [
    {"title": "Name", "align": "start", "key": "name", "sortable": False},
    {"title": "Size", "align": "end", "key": "size", "sortable": False},
    {"title": "Date", "align": "end", "key": "modified", "sortable": False},
]


def sort_by_name(e):
    return e.get("name")


def to_type(e):
    return e.get("type", "")


def to_suffix(e):
    return Path(e.get("name", "")).suffix


class ParaViewFileBrowser(TrameComponent):
    def __init__(
        self,
        server,
        prefix="pv_files",
        home=None,
        current=None,
        exclude=r"^\.|~$|^\$",
        group=r"[0-9]+\.",
    ):
        super().__init__(server)
        self._prefix = prefix

        self._enable_groups = True
        self._home_path = Path(home).resolve() if home else Path.home()
        self._current_path = Path(current).resolve() if current else self._home_path
        self.pattern_exclude = re.compile(exclude)
        self.pattern_group = re.compile(group)

        # Disable state import by default
        self.set("is_state_file", False)

        self._pxm = simple.servermanager.ProxyManager()
        self._proxy_listing = self._pxm.NewProxy("misc", "ListDirectory")
        self._proxy_directories = simple.servermanager.VectorProperty(
            self._proxy_listing, self._proxy_listing.GetProperty("DirectoryList")
        )
        self._proxy_files = simple.servermanager.VectorProperty(
            self._proxy_listing, self._proxy_listing.GetProperty("FileList")
        )

        # Initialize trame state
        self.update_listing()

    def name(self, name):
        return f"{self._prefix}_{name}"

    def set(self, name, value):
        self.state[self.name(name)] = value

    def get(self, name):
        return self.state[self.name(name)]

    def update_listing(self, selection=None):
        with self.state:
            self.set("active", -1)
            self.set("listing", self.listing)
            self.set("selected", selection)

    @property
    def enable_groups(self):
        return self._enable_groups

    @enable_groups.setter
    def enable_groups(self, v):
        self._enable_groups = v

    @property
    def listing(self):
        directories = []
        files = []
        groups = []
        g_map = {}

        self._proxy_listing.List(str(self._current_path.resolve()))
        self._proxy_listing.UpdatePropertyInformation()

        # Files + Groups
        file_listing = []
        if len(self._proxy_files) > 1:
            file_listing = self._proxy_files.GetData()
        if len(self._proxy_files) == 1:
            file_listing.append(self._proxy_files.GetData())
        file_listing = [
            file_name
            for file_name in file_listing
            if not re.search(self.pattern_exclude, file_name)
        ]
        for file_name in file_listing:
            f = self._current_path / file_name
            stats = f.stat()

            # Group or file?
            file_split = re.split(self.pattern_group, file_name)
            if self.enable_groups and len(file_split) == 2:
                # Group
                g_name = "*.".join(file_split)
                if g_name not in g_map:
                    g_entry = dict(
                        name=g_name,
                        modified=stats.st_mtime,
                        size=0,
                        files=[],
                        **GROUP,
                    )
                    g_map[g_name] = g_entry
                    groups.append(g_entry)

                g_map[g_name]["size"] += stats.st_size
                g_map[g_name]["files"].append(file_name)
                # Many need to sort files???
            else:
                # File
                files.append(
                    dict(
                        name=f.name,
                        modified=stats.st_mtime,
                        size=stats.st_size,
                        **FILE,
                    )
                )

        # Directories
        dir_listing = []
        if len(self._proxy_directories) > 1:
            dir_listing = self._proxy_directories.GetData()
        if len(self._proxy_directories) == 1:
            dir_listing.append(self._proxy_directories.GetData())
        dir_listing = [
            dir_name
            for dir_name in dir_listing
            if not re.search(self.pattern_exclude, dir_name)
        ]
        for dir_name in dir_listing:
            f = self._current_path / dir_name
            directories.append(
                dict(name=f.name, modified=f.stat().st_mtime, **DIRECTORY)
            )

        # Sort content
        directories.sort(key=sort_by_name)
        groups.sort(key=sort_by_name)
        files.sort(key=sort_by_name)

        return [
            {**e, "index": i} for i, e in enumerate([*directories, *groups, *files])
        ]

    def open_entry(self, entry):
        entry_type = entry.get("type")
        if entry_type == "directory":
            self._current_path = self._current_path / entry.get("name")
            self.update_listing()
            return entry_type, str(self._current_path)
        if entry_type == "group":
            files = entry.get("files", [])
            self.update_listing()
            return entry, [str(self._current_path / f) for f in files]
        if entry_type == "file":
            file = self._current_path / entry.get("name")
            file_name = file.name.lower()
            full_path = str(file)
            var_name = (
                "data_connectivity"
                if "connectivity_" in file_name
                else "data_simulation"
            )
            self.set(var_name, full_path)
            self.update_listing(full_path)
            return entry_type, full_path

        return None

    @property
    def active_path(self):
        entry = self.get("listing")[self.get("active")]
        return str(self._current_path / entry.get("name"))

    def set_data_connectivity(self, value=None):
        self.set("data_connectivity", value or self.active_path)

    def set_data_simulation(self, value=None):
        self.set("data_simulation", value or self.active_path)

    def goto_home(self):
        self._current_path = self._home_path
        self.update_listing()

    def goto_parent(self):
        self._current_path = self._current_path.parent
        self.update_listing()

    def open_dataset(self, entry):
        event = {}
        if to_type(entry) == "group":
            files = [str(self._current_path / f) for f in entry.get("files")]
            source = simple.OpenDataFile(files)
            representation = simple.Show(source)
            view = simple.Render()
            event = dict(
                source=source, representation=representation, view=view, type="group"
            )
        else:
            source = simple.OpenDataFile(str(self._current_path / entry.get("name")))
            representation = simple.Show(source)
            view = simple.Render()
            event = dict(
                source=source, representation=representation, view=view, type="dataset"
            )

        return event

    def select_entry(self, entry):
        with self.state as state:
            state[f"{self._prefix}_active"] = entry.get("index", 0) if entry else -1
            file_path = Path(self.active_path)

            # Check if it is a state file
            if file_path.suffix == ".json" and file_path.exists():
                state_content = json.loads(file_path.read_text())
                self.set(
                    "is_state_file",
                    all(
                        (
                            k in state_content
                            for k in [
                                "files",
                                "variables-selection",
                                "layout",
                                "data-selection",
                                "views",
                            ]
                        )
                    ),
                )
            else:
                self.set("is_state_file", False)

    def load_data_files(self, **_):
        self.set("loading", True)
        print("Load files:")
        print(" - simulation:", self.get("data_simulation"))
        print(" - connectivity:", self.get("data_connectivity"))
        self.ctrl.file_selection_load(
            self.get("data_simulation"), self.get("data_connectivity")
        )

    def import_state_file(self):
        self.set("state_loading", True)

        state_content = json.loads(Path(self.active_path).read_text())
        self.ctrl.import_state(state_content)

    def cancel(self):
        self.ctrl.file_selection_cancel()

    def loading_completed(self, valid):
        with self.state:
            self.set("loading", False)
            self.set("error", not valid)

    def ui(self):
        with v3.VCard(rounded="lg"):
            with v3.VCardTitle("File loading", classes="d-flex align-center px-3"):
                v3.VSpacer()
                v3.VBtn(
                    icon="mdi-home",
                    variant="flat",
                    size="small",
                    click=self.goto_home,
                )
                v3.VBtn(
                    icon="mdi-folder-upload-outline",
                    variant="flat",
                    size="small",
                    click=self.goto_parent,
                )
                v3.VTextField(
                    v_model=self.name("filter"),
                    hide_details=True,
                    color="primary",
                    placeholder="filter",
                    density="compact",
                    variant="outlined",
                    classes="ml-2",
                    prepend_inner_icon="mdi-magnify",
                    clearable=True,
                )

            with v3.VCardText(
                classes="rounded-lg border border-opacity-25 pa-0 mx-3 my-0 overflow-hidden"
            ):
                style_align_center = "d-flex align-center "
                with v3.VDataTable(
                    density="compact",
                    fixed_header=True,
                    headers=(self.name("headers"), HEADERS),
                    items=(self.name("listing"), []),
                    height="calc(80vh - 20rem)",
                    style="user-select: none; cursor: pointer;",
                    hover=True,
                    search=(self.name("filter"), ""),
                    items_per_page=-1,
                ):
                    v3.Template(raw_attrs=["v-slot:bottom"])
                    with v3.Template(raw_attrs=['v-slot:item="{ index, item }"']):
                        with v3.VDataTableRow(
                            index=("index",),
                            item=("item",),
                            click=(self.select_entry, "[item]"),
                            dblclick=(self.open_entry, "[item]"),
                            classes=(
                                f"{{ 'bg-grey': item.index === {self.name('active')}, 'cursor-pointer': 1 }}",
                            ),
                        ):
                            with v3.Template(raw_attrs=["v-slot:item.name"]):
                                with html.Div(classes=style_align_center):
                                    v3.VIcon(
                                        "{{ item.icon }}",
                                        size="small",
                                        classes="mr-2",
                                    )
                                    html.Div("{{ item.name }}")

                            with v3.Template(raw_attrs=["v-slot:item.size"]):
                                with html.Div(
                                    classes=style_align_center + " justify-end",
                                ):
                                    html.Div(
                                        "{{ utils.fmt.bytes(item.size, 0) }}",
                                        v_if="item.size",
                                    )
                                    html.Div(" - ", v_else=True)

                            with v3.Template(raw_attrs=["v-slot:item.modified"]):
                                with html.Div(
                                    classes=style_align_center + " justify-end",
                                ):
                                    html.Div(
                                        "{{ new Date(item.modified * 1000).toDateString() }}"
                                    )

            with v3.VCol():
                html.Label(
                    "Simulation File",
                    classes="text-subtitle-1 font-weight-medium d-block",
                )
                v3.VTextField(
                    v_model=(self.name("data_simulation"), ""),
                    density="compact",
                    variant="outlined",
                    disabled=True,
                    messages="EAM's history output on the physics grids (pg2 grids) written by EAMv2, v3, and an intermediate version towards v4 (EAMxx).",
                )
                html.Label(
                    "Connectivity File",
                    classes="text-subtitle-1 font-weight-medium d-block",
                )
                v3.VTextField(
                    v_model=(self.name("data_connectivity"), ""),
                    density="compact",
                    variant="outlined",
                    disabled=True,
                    messages="The horizontal grids used by EAM are cubed spheres. Since these are unstructed grids, QuickView needs to know how to map data to the globe. Therefore, for each simulation data file, a 'connectivity file' needs to be provided.",
                )

            v3.VDivider()
            with v3.VCardActions(classes="pa-3"):
                v3.VBtn(
                    classes="text-none",
                    variant="tonal",
                    text="Simulation",
                    prepend_icon="mdi-database-plus",
                    disabled=(
                        f"{self.name('listing')}[{self.name('active')}]?.type !== 'file'",
                    ),
                    click=self.set_data_simulation,
                )
                v3.VBtn(
                    classes="text-none",
                    text="Connectivity",
                    variant="tonal",
                    prepend_icon="mdi-vector-polyline-plus",
                    disabled=(
                        f"{self.name('listing')}[{self.name('active')}]?.type !== 'file'",
                    ),
                    click=self.set_data_connectivity,
                )
                v3.VBtn(
                    classes="text-none",
                    text="Reset",
                    variant="tonal",
                    prepend_icon="mdi-close-octagon-outline",
                    click=f"{self.name('data_connectivity')}='';{self.name('data_simulation')}='';{self.name('error')}=false",
                )
                v3.VSpacer()
                v3.VBtn(
                    border=True,
                    classes="text-none",
                    color="surface",
                    text="Cancel",
                    variant="flat",
                    click=self.cancel,
                )
                v3.VBtn(
                    disabled=(f"!{self.name('is_state_file')}",),
                    loading=(self.name("state_loading"), False),
                    classes="text-none",
                    color="primary",
                    text="Import state file",
                    variant="flat",
                    click=self.import_state_file,
                )
                v3.VBtn(
                    classes="text-none",
                    color=(f"{self.name('error')} ? 'error' : 'primary'",),
                    text="Load files",
                    variant="flat",
                    disabled=(
                        f"!{self.name('data_simulation')} || !{self.name('data_connectivity')} || {self.name('error')}",
                    ),
                    loading=(self.name("loading"), False),
                    click=self.load_data_files,
                )
