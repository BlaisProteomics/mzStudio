from setuptools import setup, find_packages



setup(name = 'mzStudio',
      version = '0.9 (Build 9)',
      author = 'Scott Ficarro, William Max Alexander',
      author_email = 'Scott_Ficarro@dfci.harvard.edu',
      packages = find_packages(),
      package_data = {'mzStudio' : ['mzStudio/image/*',
                                    'mzStudio/settings/*']},
      include_package_data = True,
      url = 'http://github.com/BlaisProteomics/mzStudio',
      description = 'Mass Spectrometry/Proteomics Data Analysis Application',
      install_requires = ['multiplierz', 'wxpython~=3.0.2.0']
      )