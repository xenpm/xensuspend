from setuptools import setup, find_packages

setup(name='xensuspend',
      version='0.0.1',
      packages=find_packages(),
      description='Xen system suspend coordinator',
      url='https://github.com/xen-troops/xensuspend',
      license='GPLv2',
      install_requires=["pyxs>=0.3"],
      entry_points={
          'console_scripts': [
                              'xensuspend = xensuspend.main:main',
                              ]
            }
    )
