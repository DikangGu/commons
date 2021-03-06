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
import errno

from twitter.common.collections import OrderedSet
from twitter.pants.base import Target, Address
from twitter.pants.python.python_chroot import PythonChroot
from twitter.pants.python.launcher import Launcher
from twitter.pants.targets import PythonTests, PythonTestSuite

class PythonTestBuilder(object):
  class InvalidDependencyException(Exception): pass
  class ChrootBuildingException(Exception): pass

  def __init__(self, targets, args, root_dir):
    self.targets = targets
    self.args = args
    self.root_dir = root_dir

  def run(self):
    return self._run_tests(self.targets)

  @staticmethod
  def get_pytest_eggs(root):
    specs = ["3rdparty/python:pytest", "3rdparty/python:py"]
    eggs = []
    for spec in specs:
      address = Address.parse(root, spec)
      target = Target.get(address)
      for dep in target.dependencies:
        for egg in dep.eggs:
          eggs.append(egg)
    return eggs

  @staticmethod
  def generate_junit_args(target):
    args = []
    xml_base = os.getenv('JUNIT_XML_BASE')
    if xml_base:
      xml_base = os.path.abspath(os.path.normpath(xml_base))
      xml_path = os.path.join(
        xml_base, os.path.dirname(target.address.buildfile.relpath), target.name + '.xml')
      try:
        os.makedirs(os.path.dirname(xml_path))
      except OSError, e:
        if e.errno != errno.EEXIST:
          raise PythonTestBuilder.ChrootBuildingException(
            "Unable to establish JUnit target: %s!  %s" % (target, e))
      args.append('--junitxml=%s' % xml_path)
    return args

  def _run_python_test(self, target):
    chroot = PythonChroot(target, self.root_dir)
    chroot.dump()
    launcher = Launcher(chroot.path())

    extra_deps = PythonTestBuilder.get_pytest_eggs(self.root_dir)
    test_args = ['-m', 'pytest']
    test_args.extend(PythonTestBuilder.generate_junit_args(target))
    test_args.extend(self.args)  # Pass any extra args in to pytest.
    sources = [os.path.join(target.target_base, source) for source in target.sources]
    return launcher.run(interpreter_args=test_args,
                        args=list(sources),
                        extra_deps=extra_deps)

  def _run_python_test_suite(self, target):
    tests = OrderedSet([])
    def _gather_deps(trg):
      if isinstance(trg, PythonTests):
        tests.add(trg)
      elif isinstance(trg, PythonTestSuite):
        for dependency in trg.dependencies:
          for dep in dependency.resolve():
            _gather_deps(dep)
    _gather_deps(target)

    for test in tests:
      rv = self._run_python_test(test)
      if rv != 0: return rv
    return 0

  def _run_tests(self, targets):
    for target in targets:
      if isinstance(target, PythonTests):
        rv = self._run_python_test(target)
      elif isinstance(target, PythonTestSuite):
        rv = self._run_python_test_suite(target)
      else:
        raise PythonTestBuilder.InvalidDependencyException(
          "Invalid dependency in python test target: %s" % target)
      if rv != 0: return rv
    return 0
