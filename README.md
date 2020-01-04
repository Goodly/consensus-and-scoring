Helpful background reading for this code:

https://docs.python.org/3/library/csv.html

https://docs.python.org/3/library/itertools.html

https://docs.python.org/3/library/operator.html#operator.itemgetter

https://docs.python.org/3/library/stdtypes.html#set-types-set-frozenset

https://docs.python.org/3/library/collections.html

https://realpython.com/python3-object-oriented-programming/

To do:

1. This is Python 2. It should be changed as needed to run under Python 3.
2. There is some Django in the code, which should be deleted.
3. Use the standard library CSV reader to open and read TagWorks CSV files.
5. Use sort with itertools itemgetter to sort the CSV rows.
4. Use the itertools groupby function to iterate over the CSV rows.

To don't:

1. Please don't incorporate Numpy or Pandas in this code base.
2. Please don't install a virtualenv in this repo and commit it.
   Your virtualenv should be outside of this repo tree.
