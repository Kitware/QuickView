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

    return parser.parse_known_args()[0]
