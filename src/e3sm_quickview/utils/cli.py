from pathlib import Path


def configure_and_parse(parser):
    parser.add_argument(
        "-cf",
        "--conn",
        nargs="?",
        help="the nc file with connnectivity information",
    )
    parser.add_argument(
        "-df",
        "--data",
        help="the nc file with data/variables",
    )
    parser.add_argument(
        "-sf",
        "--state",
        nargs="?",
        help="state file to be loaded",
    )
    parser.add_argument(
        "-wd",
        "--workdir",
        default=str(Path.cwd().resolve()),
        help="working directory (to store session data)",
    )
    parser.add_argument(
        "--user-home",
        dest="user_home",
        action="store_true",
        help="Use user home as home for file browsing",
    )
    parser.add_argument(
        "--fast",
        dest="fast",
        action="store_true",
        help="Use a single vtkRenderWindow to share GPU memory",
    )
    parser.add_argument(
        "--perf",
        dest="perf",
        action="store_true",
        help="Emit performance timing on stderr ([PERF] lines). Used to "
        "diagnose where slider-tick cost is going — reader I/O, pipeline, "
        "rendering, web layer, etc.",
    )

    return parser.parse_known_args()[0]
