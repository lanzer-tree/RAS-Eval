# nuXmv

This is version 2.1.0 of the nuXmv symbolic model checker.

- [Useful Links](#useful-links)
- [Files in nuXmv Distribution](#files-in-nuxmv-distribution)


nuXmv is a symbolic model checker for the analysis of synchronous
finite-state and infinite-state systems.

nuXmv extends NuSMV along two main directions:

* for the finite-state case, nuXmv features a strong verification
  engine based on state-of-the-art SAT-based algorithms

* for the infinite-state case, nuXmv features SMT-based verification
  techniques, implemented through a tight integration with MathSAT5.

nuXmv is currently licensed in binary form, for non-commercial or
academic purposes. See [LICENSE.txt](./LICENSE.txt) for details.

Inquiries about other usages of nuXmv should be addressed to
<es-tools-board@fbk.eu>.

Visit [nuxmv.fbk.eu](https://nuxmv.fbk.eu) for more detailed information
and download.


## Useful Links

* Feature requests and bug reports: <nuxmv-users@list.fbk.eu>
* Frequently asked questions: [FAQ](https://nuxmv.fbk.eu/faq.html)


## Files in nuXmv Distribution

[NEWS.md](./NEWS.md)
: A file with the news about this release.

[LICENSE.txt](./LICENSE.txt)
: License file.

`bin/nuXmv`
: The nuXmv executable.

`share/nuxmv/master.nuxmv`
: An example of a script file for initializing nuXmv. To use it,
  `NUXMV_LIBRARY_PATH` shall refer to the full path of the directory where
  this file resides.

`share/nuxmv/contrib`
: A direcotry containing scripts for converting from/to several formats.

`doc/user-man/nuxmv.pdf`
: The PDF of the nuXmv User Manual.

`examples/`
: A collection of examples/files used in several papers about nuXmv.
