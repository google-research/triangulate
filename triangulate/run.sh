# When adding an expression, the agent should make some effort to make
# sure it is interpretable:  that its imports and free variables are
# satisfed.  It currently does not do so, but we may wish to do so
# in the ?near? future, so I have added this note and am keeping the
# following code to remind me of this task.
# TODO(etbarr):  Add best effort interpretability support to triangulate.
ml_python triangulate.py -- -p quoter.py -b "5" -i "1 == 1" -t 34 -m 1