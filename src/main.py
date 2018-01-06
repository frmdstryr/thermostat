# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the MIT License.

The full license is in the file COPYING.txt, distributed with this software.

Created on Sep 14, 2017

@author: jrm
"""
import sys
import os
# import logging
# # ### Comment out to disable profiling
# import cProfile
# pr = cProfile.Profile()
# pr.enable()
# # End profiling
#
#
# def init_logging():
#     root = logging.getLogger()
#     root.setLevel(logging.DEBUG)
#
#     ch = logging.StreamHandler(sys.stdout)
#     ch.setLevel(logging.DEBUG)
#     formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
#     ch.setFormatter(formatter)
#     root.addHandler(ch)


def main():
    """ Called by PyBridge.start()
    """
    #init_logging()
    #: If we don't our code goes away
    #os.environ['TMP'] = os.path.join(sys.path[0], '../tmp')
    #from charts.android.factories import install
    #install()

    from enamlnative.android.app import AndroidApplication
    app = AndroidApplication(
        #dev='remote',
        load_view=load_view
    )
    app.start()


def load_view(app):
    import enaml
    with enaml.imports():
        import view
        if app.view:
            #: This is a reload
            reload(view)
        app.view = view.ContentView()
    app.show_view()
#     app.timed_call(20000, dump_stats)
#
#
# def dump_stats():
#     try:
#         pr.disable()
#         import pstats, StringIO
#         for sort_by in ['cumulative', 'time']:
#             s = StringIO.StringIO()
#             ps = pstats.Stats(pr, stream=s).sort_stats(sort_by)
#             ps.print_stats(0.3)
#             print s.getvalue()
#     except:
#         pass
