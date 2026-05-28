import sys

from test_paths import resolve_overmind_root

OVERMIND_ROOT = resolve_overmind_root()
if str(OVERMIND_ROOT) not in sys.path:
    sys.path.insert(0, str(OVERMIND_ROOT))
