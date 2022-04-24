#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Spectrum Analyzer
# GNU Radio version: 3.8.1.0

from gnuradio import blocks
from gnuradio import fft
from gnuradio.fft import window
from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import gr, blocks
from gnuradio import uhd
import threading
import time
import requests
import pmt

class top_block(gr.top_block):

    def __init__(self, radioNum):
        gr.top_block.__init__(self, "Spectrum Analyzer")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = int(300e3)
        self.center_freq = center_freq = 900e6
        self.radio_num = radioNum

        # Create custom PMT metadata containing the assigned radio number
        key0 = pmt.intern("radio_num")
        val0 = pmt.from_long(self.radio_num)
        extra_meta = pmt.make_dict()
        extra_meta = pmt.dict_add(extra_meta, key0, val0)

        ##################################################
        # Blocks
        ##################################################
        self.uhd_usrp_source_0 = uhd.usrp_source(
            ",".join(("", "")),
            uhd.stream_args(
                cpu_format="fc32",
                args='peak=0.003906',
                channels=list(range(0,1)),
            ),
        )
        self.uhd_usrp_source_0.set_center_freq(center_freq, 0)
        self.uhd_usrp_source_0.set_gain(28, 0)
        self.uhd_usrp_source_0.set_antenna('RX2', 0)
        self.uhd_usrp_source_0.set_bandwidth(samp_rate, 0)
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        # No synchronization enforced.
        self.fft_vxx_0 = fft.fft_vcc(1024, True, window.blackmanharris(1024), True, 1)
        self.blocks_vector_to_stream_0 = blocks.vector_to_stream(gr.sizeof_gr_complex*1, 1024)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, 1024)
        self.blocks_file_meta_sink_0 = blocks.file_meta_sink(gr.sizeof_gr_complex*1, f'./sample{self.radio_num}.dat', samp_rate, 1, blocks.GR_FILE_FLOAT, True, 300000, extra_meta, False)
        self.blocks_file_meta_sink_0.set_unbuffered(False)



        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_stream_to_vector_0, 0), (self.fft_vxx_0, 0))
        self.connect((self.blocks_vector_to_stream_0, 0), (self.blocks_file_meta_sink_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.blocks_vector_to_stream_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_stream_to_vector_0, 0))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)
        self.uhd_usrp_source_0.set_bandwidth(self.samp_rate, 0)

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, freq):
        self.center_freq = freq
        self.uhd_usrp_source_0.set_center_freq(self.center_freq, 0)

    def MQP_HTTP_Parser(self):
        while True:
            freq1 = int((requests.get(f'http://spectrumobservatory.wpi.edu/freq{self.radio_num}')).content)
            if(freq1 != self.get_center_freq): # Only set frequency if it is different (save on overhead)
                self.set_center_freq(freq1)
            time.sleep(5)

    def startThread(self):
        self.t1 = threading.Thread(target = self.MQP_HTTP_Parser)
        self.t1.daemon = True
        self.t1.start()


## NOTE: GNURadio generated main function not used
def main(top_block_cls=top_block, options=None):
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()
        print("Exiting")
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()
    tb.startThread()
    
    try:
        input('Press Enter to quit: ')
    except EOFError:
        pass

    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
