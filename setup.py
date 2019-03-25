from distutils.core import setup

setup(name='xensuspend',
      version='0.0.1',
      packages=['xensuspend'],
      description='Xen system suspend coordinator',
      url='https://github.com/xen-troops/xensuspend',
      license='GPLv2',
      install_requires=["pyxs>=0.3"],
      scripts=['bin/xensuspend']
    )
