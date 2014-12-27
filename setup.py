
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


class Tox(TestCommand):
    """ Wrapper to run tox when calling python setup.py test """
    user_options = [('tox-args=', 'a', "Arguments to pass to tox")]
    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = None
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import tox
        import shlex
        errno = tox.cmdline(args=shlex.split(self.tox_args or ""))
        sys.exit(errno)


setup(
    name='Tygs',
    version="0.1.0",
    author='Sam et Max',
    author_email='lesametlemax@gmail.com',
    py_modules=['tygs'],
    license='BSD Licence',
    long_description=open('README.rst').read(),
    description="Pure Python asynchronous Web framework with PUB/SUB, RPC, tasks queues and multiprocessing packed in a nice API.",
    url='http://github.com/sametmax/tygs',
    keywords="python, asynchronous, web",
    include_package_data=True,
    install_requires=['klein'],
    extra_requires={
        'testing': ['tox', 'pytest-cov', 'mock'],
    },
    tests_require=['tox'],
    cmdclass = {'test': Tox},
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
    ],
)
