from disco.test import DiscoJobTestFixture, DiscoTestCase
from disco.core import result_iterator
from disco.func import map_input_stream, disco_output_stream

def map_input_stream1(stream, size, url, params):
    r = stream.read()
    fd = cStringIO.StringIO('a' + r)
    return fd, len(r) + 1, 'a:%d' % Task.partitions

def map_input_stream2(stream, size, url, params):
    r = stream.read()
    fd = cStringIO.StringIO('b' + r)
    return fd, len(r) + 1, url + 'b:%d' % Task.partitions

def reduce_output_stream1(stream, id, url, params):
    return 'fd', 'url:%d' % Task.partitions

def reduce_output_stream2(stream, id, url, params):
    assert stream == 'fd' and url == 'url:%d' % Task.partitions
    path, url = Task.outurls(id)
    return disco.fileutils.AtomicFile(path, 'w'), url.replace('disco://', 'foobar://')

class StreamsTestCase(DiscoJobTestFixture, DiscoTestCase):
    inputs = ['apple', 'orange', 'pear']
    map_input_stream = [map_input_stream, map_input_stream1, map_input_stream2]
    reduce_output_stream = [reduce_output_stream1, reduce_output_stream2, disco_output_stream]

    def getdata(self, path):
        return path

    @staticmethod
    def map_reader(stream, size, url):
        n = Task.partitions
        assert url == 'a:%db:%d' % (n, n)
        yield stream.read()

    @staticmethod
    def map(e, params):
        return [(e, '')]

    @staticmethod
    def reduce(iter, params):
        for k, v in iter:
            yield 'red:' + k, v

    @property
    def results(self):
        def input_stream(stream, size, url, params):
            self.assert_(url.startswith('foobar://'))
            return stream, size, url.replace('foobar://', 'disco://')
        return result_iterator(self.job.wait(), input_stream=[input_stream, map_input_stream])

    def runTest(self):
        for k, v in self.results:
            self.assert_(k.startswith('red:ba'))
            self.assert_(k[6:] in self.inputs)
