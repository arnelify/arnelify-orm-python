from setuptools import setup, find_packages, Extension

ffi = Extension(
  'arnelify-orm-ffi',
  sources=['arnelify_orm/src/ffi.cpp'],
  language='c++',
  extra_compile_args=['-std=c++2b', '-w'],
  include_dirs=['/usr/include', '/usr/include/jsoncpp/json'],
  extra_link_args=['-ljsoncpp', '-lmysqlclient']
)

setup(
  name="arnelify_orm",
  version="0.7.3",
  author="Arnelify",
  description="Minimalistic dynamic library which is an ORM written in C and C++.",
  url='https://github.com/arnelify/arnelify-orm-python',
  keywords="arnelify arnelify-orm-python arnelify-orm",
  packages=find_packages(),
  license="MIT",
  install_requires=["cffi", "setuptools", "wheel"],
  long_description=open("README.md", "r", encoding="utf-8").read(),
  long_description_content_type="text/markdown",
  classifiers=[
    "Programming Language :: Python :: 3",
  ],
  ext_modules=[ffi],
)