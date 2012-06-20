# -*- coding: utf-8 -*-

#
# Copyright (c) 2012 by Fredrik <Fredrik@FjeldWeb.no>
# Borrowed parts from announce_url_title.py by xt.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#
# If someone posts a URL with an image-suffix (or any other suffix, if set)
# this script downloads the file to a set folder and logs it in a csv-file.
#
# Change buffers the script looks in:
# "/set plugins.var.python.get_image.buffers server.#channel,server.#otherchannel"
# Change direcory the script downloads to (remember the last slash):
# "set plugins.var.python.get_image /home/foo/bar/"
#

# TODO:
# Use the hook_process(_hashtable) to download the image
# http://dev.weechat.org/post/2012/01/18/URL-transfer-in-API

# History:
# 2012-06-19, Fredrik
#    version 0.1: initial

from urllib2 import Request, urlopen, URLError, HTTPError # Used to download the file
import re # Used to check if the url is a image file
import datetime # Used to record a timestamp in the log-file
import os
import weechat
w = weechat

SCRIPT_NAME    = "get_image"
SCRIPT_AUTHOR  = "Fredrik <Fredrik@FjeldWeb.no>"
SCRIPT_VERSION = "0.1"
SCRIPT_LICENSE = "GPL3"
SCRIPT_DESC    = "Downloads images posted in channels"

settings = {
    "buffers"   : 'efnet.#testing,freenode.#testing',  # Comma separated list of buffers to look in
    'directory' : '/home/fredrik/ircimages/',          # Directory to which the images are downloaded
    "suffix"    : 'jpg,gif,png',                       # Comma separated list of filetypes to download
}

octet = r'(?:2(?:[0-4]\d|5[0-5])|1\d\d|\d{1,2})'
ipAddr = r'%s(?:\,.%s){3}' % (octet, octet)
# Base domain regex off RFC 1034 and 1738
label = r'[0-9a-z][-0-9a-z]*[0-9a-z]?'
domain = r'%s(?:\.%s)*\.[a-z][-0-9a-z]*[a-z]?' % (label, label)
urlRe = re.compile(r'(\w+://(?:%s|%s)(?::\d+)?(?:/[^\])>\s]*)?)' % (domain, ipAddr), re.I)

# Downloads the image
def download_img(img_url, nick):
                
    url_array = img_url.split("/")
    imgname = url_array[-1]
    
    req = Request(img_url)
    # Open the url
    try:
        f = urlopen(req)
        w.prnt("", "downloading " + img_url)
        
        dir = w.config_get_plugin('directory')
        
        # Check if there already is exists a log-file
        if os.path.isfile(dir + "log.csv"):
            # Figure out the filenumber
            log_file = open(dir + "log.csv", "r")
            loglines = log_file.readlines()
            log_file.close()
            log_lastline = loglines[-1]
            log_line_list = log_lastline.split(",")
            filenumber = (int(log_line_list[0]) + 1)
            filenumber = '{0:05}'.format(filenumber)
            filenumber = str(filenumber)
        else:
            filenumber = "00001"
        
        # Get file extention
        imgname_list = imgname.split(".")
        ext = imgname_list[-1]
        
        
        # Open our local file for writing
        local_file = open(dir + filenumber + "." + ext, "wb")
        # Write the local file
        local_file.write(f.read())
        local_file.close()
        
        # Logging
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        # Open the download-log
        log_file = open(dir + "log.csv", "a")
        # Write to the log-file
        log_file.write(filenumber + ",\"" + timestamp + "\",\"" + img_url + "\",\"" + nick + "\"\n")
        log_file.close()
        
        return w.WEECHAT_RC_OK
    
    # Handle errors
    except HTTPError, e:
        w.prnt( "HTTP Error:",e.code , img_url )
    except URLError, e:
        w.prnt( "URL Error:",e.reason , img_url )
    

# Recieves the message with the URL
def take_url(data, buffer, time, tags, displayed, highlight, prefix, message):
    global buffer_name, urls, ignore_buffers
    
    # Gets the nick of the poster (in an ugly way, I'm sure this can be done more elegant)
    tags = tags.split(",")
    nick_tag = tags[2].split("_")
    nick = nick_tag[1]
    
    # Do not trigger on filtered lines and notices
    if displayed == '0' or prefix == '--':
        return w.WEECHAT_RC_OK
    
    # Checks if the message was recieved from an accepted buffer
    msg_buffer_name = w.buffer_get_string(buffer, "name")
    found = False
    for active_buffer in w.config_get_plugin('buffers').split(','):
        if active_buffer.lower() == msg_buffer_name.lower():
            found = True
            buffer_name = msg_buffer_name
            break
            
    if not found:
        w.prnt("", "url found, but not in correct buffer.")
        return w.WEECHAT_RC_OK
    
    for url in urlRe.findall(message):
        url = url.replace("'", "%27") # Escape the ' char
        
        # Checks if the url provided ends with the predefined suffixes
        filetypes = tuple(w.config_get_plugin('suffix').split(','))
        if url.endswith(filetypes):
            download_img(url, nick) # Sends the image url to be downloaded
        else:
            return w.WEECHAT_RC_OK
    
    return w.WEECHAT_RC_OK


if __name__ == '__main__' and w.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, '', ''):
    for option, default_value in settings.iteritems():
        if not w.config_is_set_plugin(option):
            w.config_set_plugin(option, default_value)
    w.hook_print("", "", "://", 1, "take_url", "")