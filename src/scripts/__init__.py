__import__("pkg_resources").declare_namespace(__name__)

from sys import argv
from subprocess import Popen
from platform import system
from infi.execute import execute_assert_success
from sys import exit


def test():
    from logging import basicConfig, getLogger, DEBUG
    from subprocess import Popen
    from os import path, name
    basicConfig(level=DEBUG)
    python = path.join('dist', 'bin', 'python%s' % ('.exe' if name == 'nt' else ''))
    getLogger(__name__).info("testing %s" % python)
    assert Popen([python, path.join("tests", "test_ssl.py")]).wait() == 0
    assert Popen([python, path.join("tests", "test_ctypes.py")]).wait() == 0


def build(argv=' '.join(argv[1:])):
    from sys import maxsize
    from os import environ
    environ = environ.copy()
    buildout_file = 'buildout-build.cfg'
    if system() == 'Linux':
        from platform import dist, linux_distribution
        _, version, distid = linux_distribution()
        dist_name = dist()[0].lower()
        if dist_name == 'ubuntu':
            buildout_file = 'buildout-build-ubuntu.cfg'
        if dist_name in ['redhat', 'centos'] and maxsize > 2**32:
            buildout_file = 'buildout-build-redhat-64bit.cfg'
        if dist_name in ['suse'] and version in ['10']:
            buildout_file = 'buildout-build-suse-10.cfg'
    elif system() == 'Darwin':
        from platform import mac_ver
        environ["MACOSX_DEPLOYMENT_TARGET"] = '.'.join(mac_ver()[0].split('.', 2)[:2])
        if 'version 5.' in execute_assert_success(["gcc", "--version"]).get_stdout():
            buildout_file = 'buildout-build-osx-xcode-5.cfg'
        elif 'version 6.' in execute_assert_success(["gcc", "--version"]).get_stdout():
            buildout_file = 'buildout-build-osx-xcode-6.cfg'
        else:
            buildout_file = 'buildout-build-osx.cfg'
    elif system() == 'Windows':
        if maxsize > 2**32:
            buildout_file = 'buildout-build-windows-64bit.cfg'
        else:
            buildout_file = 'buildout-build-windows.cfg'
    elif system() == "SunOS":
        if 'sparc' in execute_assert_success(["isainfo"]).get_stdout().lower():
            buildout_file = 'buildout-build-solaris-sparc.cfg'
        elif '64' in execute_assert_success(["isainfo", "-b"]).get_stdout():
            buildout_file = 'buildout-build-solaris-64bit.cfg'
        else:
            pass #TODO support 32 bit
    elif system() == "AIX":
        buildout_file = 'buildout-build-aix.cfg'
    command = "./bin/buildout -c {} {}".format(buildout_file, argv)
    print 'executing "%s"' % command
    process = Popen(command.split(), env=environ)
    stdout, stderr = process.communicate()
    exit(process.returncode)

def pack(argv=' '.join(argv[1:])):
    command = './bin/buildout -c buildout-pack.cfg %s' % argv
    if system() == 'Windows':
        command = './bin/buildout -c buildout-pack-windows.cfg %s' % argv
    elif system() == "AIX":
        command = './bin/buildout -c buildout-pack-aix.cfg %s' % argv
    print 'executing "%s"' % command
    process = Popen(command.split())
    stdout, stderr = process.communicate()
    exit(process.returncode)

def clean(argv=' '.join(argv[1:])):
    from os.path import abspath, pardir, exists
    from os import mkdir, remove, path
    from glob import glob
    from shutil import rmtree, move

    sep = '/'
    filepath = __file__.replace(path.sep, '/')
    base = abspath(sep.join([filepath, pardir, pardir, pardir]))
    dist = sep.join([base, 'dist'])
    parts = sep.join([base, 'parts'])
    installed_file = sep.join([base, '.installed-build.cfg'])

    print "base = %s" % repr(base)

    for tar_gz in glob(sep.join([base, '*tar.gz'])):
        print "rm %s" % tar_gz
        remove(tar_gz)

    print "rm -rf %s" % repr(dist)
    _catch_and_print(rmtree, *[dist])

    src = sep.join([parts, 'buildout'])
    dst = sep.join([base, 'buildout'])

    print "mv %s %s" % (repr(src), repr(dst))
    _catch_and_print(move, *[src, dst])

    print "rm %s" % repr(installed_file)
    if exists(installed_file):
        remove(installed_file)

    print "rm -rf %s" % repr(parts)
    _catch_and_print(rmtree, *[parts])

    print "mkdir %s" % repr(parts)
    _catch_and_print(mkdir, *[parts])

    dst = sep.join([parts, 'buildout'])
    src = sep.join([base, 'buildout'])
    print "mv %s %s" % (repr(src), repr(dst))
    _catch_and_print(move, *[src, dst])


def _catch_and_print(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except (OSError, IOError), e:
        print e

