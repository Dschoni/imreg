

from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize
import numpy

extensions = [
    Extension("interpolation", ["_interpolation.pyx"], include_dirs=[numpy.get_include()]), '.']

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
      include_dirs=[numpy.get_include(),'.'],
      zip_safe=False)
