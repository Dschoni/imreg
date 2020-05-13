# import os


# def configuration(parent_package='', top_path=None):
#     from numpy.distutils.misc_util import Configuration
#     config = Configuration('imreg', parent_package, top_path)
#     return config

# if __name__ == "__main__":
#     from numpy.distutils.core import setup

#     config = configuration(top_path='').todict()
#     setup(**config)
    

# from setuptools import Extension, setup



#     # Everything but primes.pyx is included here.
#     Extension("*", ["*.pyx"],
#         include_dirs=[...],
#         libraries=[...],
#         library_dirs=[...]),
# ]
# setup(
#     name="My hello app",
#     ext_modules=cythonize(extensions),
# )

from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize

extensions = [
    Extension("interpolation", ["primes.pyx"])]

setup(name='imreg',
      version='0.1.1',
      description='Image registration tools',
      url='https://github.com/Dschoni/imreg',
      author='Jonathan Schock',
      author_email='jonathan.schock@directconversion.com',
      license='MIT',
      packages=find_packages(),
# 	  package_data={'':['*.dll']},
      ext_modules=cythonize(extensions),
      zip_safe=False)
