# ==================================================================================================
# Copyright 2011 Twitter, Inc.
# --------------------------------------------------------------------------------------------------
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this work except in compliance with the License.
# You may obtain a copy of the License in the LICENSE file, or at:
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==================================================================================================

import os

from . import Command

from twitter.common.collections import OrderedSet

from twitter.pants import is_python
from twitter.pants.base import Address, Target
from twitter.pants.targets import PythonBinary
from twitter.pants.python import PythonChroot
from twitter.pants.python.launcher import Launcher

import traceback

class Py(Command):
  """Python chroot manipulation."""

  __command__ = 'py'

  def setup_parser(self, parser):
    parser.set_usage("\n"
                     "  %prog py (options) [spec] args\n")
    parser.disable_interspersed_args()
    parser.epilog = """Dumps the chroot of the specified target."""

  def __init__(self, root_dir, parser, argv):
    Command.__init__(self, root_dir, parser, argv)

    if not self.args:
      self.error("A spec argument is required")

    try:
      address = Address.parse(root_dir, self.args[0])
      target = Target.get(address)
    except:
      self.error("Invalid target in %s" % self.args[0])

    if not target:
      self.error("Target %s does not exist" % address)
    self.target = target
    self.args.pop(0)

  def execute(self):
    print "Build operating on target: %s" % self.target
    executor = PythonChroot(self.target, self.root_dir)
    executor.dump()
    binary = None
    if isinstance(self.target, PythonBinary):
      binary = os.path.join(executor.path(), '__main__.py')
    launcher = Launcher(executor.path(), binary)
    launcher.run(args=list(self.args))
