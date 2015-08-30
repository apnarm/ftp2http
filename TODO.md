* Replace a lot of the HTTP parts with [requests](https://pypi.python.org/pypi/requests)
  * [python-swiftclient](https://pypi.python.org/pypi/python-swiftclient) actually internally uses [requests](https://pypi.python.org/pypi/requests)
  * We should be able to just `.request("PUT", files=...)`
* Publish a Python Wheel

See also:
    
    grin "(TODO|XXX)"
