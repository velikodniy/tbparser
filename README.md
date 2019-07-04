# tbparser [![Build Status](https://travis-ci.org/velikodniy/tbparser.svg?branch=master)](https://travis-ci.org/velikodniy/tbparser)

A simple library for parsing Tensorboard logs.

## Installation

You can install the library as usual with `pip`:

```
pip install git+https://github.com/velikodniy/tbparser.git
```

## Usage

The main class is `tbparser.summary_reader.SummaryReader`.
Creating an instance:

```python
from tbparser.summary_reader import SummaryReader
logdir = 'my_logs'
reader = SummaryReader(logdir)
```

It will try to parse _every_ file in the logs directory and its subdirectories.

Also you can add a filter on tags if you interested in only specific events.
Just list the tags in the `tag_filter` argument.

```python
reader = SummaryReader(logdir, tag_filter=['loss'])
```

In this case the reader will yield only events with tag `'loss'`.

By default reader yields only scalar values.
It's because the argument `types` is set to ['scalar'].
You can list all the types you interested in.
All the unlisted types will be ignored.

The supported types are:

- `scalar` — a scalar value;
- `image` — a decoded image (Numpy array);
- `image_raw` — a raw image (bytes of PNG, for example).

Other types will be added later (maybe).

Note that if you subscribes both on `image` and `image_raw`, any particular image event will produce two yields.

There is also an argument `stop_on_error` that is False by default.

After creating you can use the reader as an ordinary iterator:

```
while item in reader:
  do_something(item)
```

`item` is an instance of `tbparser.summary_reader.SummaryItem`. It is a named tuple actually with the fillowing keys:

- `tag`,
- `step`,
- `wall_time`,
- `value`,
- `type` — a string with the type name (e.g., `'scalar'`).
