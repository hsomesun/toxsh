import sys,time,random
import json

from PyQt5.QtCore import *
from PyQt5.QtNetwork import *

import qtutil
from qtoxkit import *
# from toxsocket import *
from toxtunutils import *
# from srudp import *

class ToxTunSrv(QObject):
    def __init__(self, parent = None):
        super(ToxTunSrv, self).__init__(parent)
        return

class ToxTunFileSrv(ToxTunSrv):
    def __init__(self, config_file = './toxtun.ini', parent = None):
        super(ToxTunFileSrv, self).__init__(parent)
        
        self.cfg = ToxTunConfig(config_file)
        self.toxkit = None # QToxKit
        self.cons = {}  # peer => con
        self.chans = {} # sock => chan, chanosrv_%d => chan
        #self.host = '127.0.0.1'
        #self.port = 80
        self.chano = 7
        self.cmdno = 7  # depcreated
        
        return

    def start(self):
        tkname = self.cfg.srvname
        # toxkit = QToxKit('anon', True)
        toxkit = QToxKit(tkname, True)

        toxkit.connected.connect(self._toxnetConnected, Qt.QueuedConnection)
        toxkit.disconnected.connect(self._toxnetDisconnected, Qt.QueuedConnection)
        toxkit.friendAdded.connect(self._toxnetFriendAdded, Qt.QueuedConnection)
        toxkit.friendConnectionStatus.connect(self._toxnetFriendConnectionStatus, Qt.QueuedConnection)
        toxkit.friendConnected.connect(self._toxnetFriendConnected, Qt.QueuedConnection)
        toxkit.newMessage.connect(self._toxnetFriendMessage, Qt.QueuedConnection)
        toxkit.fileRecv.connect(self._toxnetFileRecv, Qt.QueuedConnection)
        toxkit.fileRecvControl.connect(self._toxnetFileRecvControl, Qt.QueuedConnection)
        toxkit.fileRecvChunk.connect(self._toxnetFileRecvChunk, Qt.QueuedConnection)
        toxkit.fileChunkRequest.connect(self._toxnetFileChunkRequest, Qt.QueuedConnection)

        self.toxkit = toxkit
        
        return

    def _toxnetConnected(self):
        qDebug('here')
        toxsock = self.sender()
        #ses = self.cons[toxsock]
        #ses.tox_connected = True

        #ses.sock.readyRead.emit()
        return
    
    def _toxnetDisconnected(self):
        qDebug('here')
        return

    def _toxnetFriendAdded(self, fid):
        qDebug('hehe:fid=' + fid)
        #con = self.toxcons[fid]

        con = ToxConnection()
        con.peer = fid

        self.cons[fid] = con
        
        return

    def _toxnetFriendConnectionStatus(self, fid, status):

        return
    
    def _toxnetFriendConnected(self, fid):
        qDebug('herhe:fid=' + fid)
        # 只重启动srv端时，有可能好友还在线。
        if fid not in self.cons:
            con = ToxConnection()
            con.peer = fid
            self.cons[fid] = con
            pass

        return

    def _nextChano(self):
        self.chano = self.chano +2
        return self.chano

    def _nextCmdno(self):
        self.cmdno = self.cmdno +1
        return self.cmdno

    def _toxnetFileRecv(self, friend_id, file_number, file_size, file_name):
        qDebug(file_name)

        # con = self.cons[friend_id]
        con = None
        for id in self.cons:
            if type(id) == str and id[0:64] == friend_id:
                con = self.cons[id]
                break

        if con is None: qDebug('warning con not found')

        curr_self_file_number = con.self_file_number
        if con.peer_file_number != -1:
            qDebug('warning, maybe reuse file channel: %d,%d' % (con.peer_file_number, con.self_file_number))
            # close current con.peer_file_number
            # self.toxkit.fileControl(con.peer, con.peer_file_number, Tox.FILE_CONTROL_CANCEL)
            # self.toxkit.fileControl(con.peer, con.self_file_number, Tox.FILE_CONTROL_CANCEL)
            self.toxkit.fileControl(con.peer, con.self_file_number, Tox.FILE_CONTROL_PAUSE)
            con.reqchunks = []
        
        con.peer_file_number = file_number
        peer_file_to_con_key = 'peer_file_to_con_%d_%s' % (file_number, friend_id)
        self.cons[peer_file_to_con_key] = con

        idprefix = friend_id[0:6]
        srv_file_name = 'toxtunfilesrv_%s_toxfilesock' % idprefix
        srv_file_size = pow(2, 56)
        srv_file_number = self.toxkit.fileSend(con.peer, srv_file_size, srv_file_name)
        con.self_file_number = srv_file_number
        # srv_file_size -= 123456
        # srv_file_number2 = self.toxkit.fileSend(con.peer, srv_file_size, srv_file_name)
        srv_file_number2 = -123
        qDebug('new srv file %d,%d' % (srv_file_number, srv_file_number2))

        self_file_to_con_key = 'self_file_to_con_%d_%s' % (srv_file_number, con.peer[0:64])
        self.cons[self_file_to_con_key] = con
        
        self.toxkit.fileControl(friend_id, file_number, 0)
        
        # segs = file_name.split('_')
        # qDebug(str(segs))

        # cmdno = int(segs[1])
        # host = segs[2]
        # port = int(segs[3])
        
        # sock = QTcpSocket()
        # sock.setReadBufferSize(1234)
        # sock.connected.connect(self._onTcpConnected)
        # sock.disconnected.connect(self._onTcpDisconnected)
        # sock.readyRead.connect(self._onTcpReadyRead)
        # sock.error.connect(self._onTcpError)
        # sock.connectToHost(QHostAddress(host), port)
        
        # chan = ToxTunFileChannel(con, sock)
        # chan.host = host
        # chan.port = port
        # chan.chano = self._nextChano()
        # chan.cmdno = cmdno
        # chan.peer_file_number = file_number
        
        # self.chans[sock] = chan
        # self.chans[chan.chano] = chan
        # self.chans[file_name] = chan

        # srv_file_name = 'toxtunfilesrv_%d_%s_%d_toxfilesock' % (chan.cmdno, chan.host, chan.port)
        # srv_file_size = pow(2, 56)
        # srv_file_number = self.toxkit.fileSend(con.peer, srv_file_size, srv_file_name)
        # chan.self_file_number = srv_file_number
        # qDebug('new srv file %d' % srv_file_number)

        # peer_file_to_chan_key = 'peer_file_to_chan_%d_%s' % (file_number, con.peer[0:64])
        # self.chans[peer_file_to_chan_key] = chan

        # self_file_to_chan_key = 'self_file_to_chan_%d_%s' % (srv_file_number, con.peer[0:64])
        # self.chans[self_file_to_chan_key] = chan

        # self.toxkit.fileControl(friend_id, file_number, 0)

        return

    
    def _toxnetFileRecvControl(self, friend_id, file_number, control):
        qDebug('here')
        print((friend_id, file_number, control))

        if control == 0:
            qDebug('resumed')
            # self.toxkit.fileControl(friend_id, file_number, 1)
        elif control == 1:
            qDebug('paused')
        elif control == 2:
            qDebug('canceled')

        return

    def _toxnetFileRecvChunk(self, friend_id, file_number, position, data):
        qDebug('here')
        peer_file_to_con_key = 'peer_file_to_con_%d_%s' % (file_number, friend_id[0:64])
        con = self.cons[peer_file_to_con_key]
        # print(friend_id, file_number, position, data)

        jspkt = data.lstrip()
        pkt = json.JSONDecoder().decode(jspkt)
        ptype = pkt['type']
        qDebug(str(jspkt))

        if ptype == 'CONNECT':
            host = pkt['host']
            port = pkt['port']
            
            sock = QTcpSocket()
            sock.setReadBufferSize(1234)
            sock.connected.connect(self._onTcpConnected, Qt.QueuedConnection)
            sock.disconnected.connect(self._onTcpDisconnected, Qt.QueuedConnection)
            sock.readyRead.connect(self._onTcpReadyRead, Qt.QueuedConnection)
            # connect() failed between error(QAbstractSocket::SocketError) and unislot()
            # sock.error.connect(self._onTcpError, Qt.QueuedConnection)
            sock.error.connect(self._onTcpError)
            sock.connectToHost(QHostAddress(host), port)
            
            chan = ToxTunFileChannel(con, sock)
            chan.host = host
            chan.port = port
            chan.chanocli = pkt['chcli']
            chan.chanosrv = self._nextChano()
            
            self.chans[sock] = chan
            self.chans['chanosrv_%d' % chan.chanosrv] = chan

            npkt = pkt
            npkt['chsrv'] = chan.chanosrv
            njspkt = json.JSONEncoder().encode(npkt)
            nfjspkt = '%1371s' % njspkt

            if len(con.reqchunks) > 0:
                reqinfo = con.reqchunks.pop(0)
                bret = self.toxkit.fileSendChunk(con.peer, con.self_file_number, reqinfo[2], nfjspkt)
                qDebug(str(bret))
            pass
        elif ptype == 'CLOSE':
            chanosrv = pkt['chsrv']
            chan = self.chans['chanosrv_%d' % chanosrv]
            chan.peer_close = True
            self._toxchanPromiseCleanup(chan)
            pass
        elif ptype == 'WRITE':
            chanosrv = pkt['chsrv']
            chan = self.chans['chanosrv_%d' % chanosrv]
            self._tcpWrite(chan, pkt['data'])
            pass
        else: qDebug('ptype error: %s' % ptype)
        
        
        # qDebug(str(data))
        # plen = data[0:4].lstrip()
        # plen = int(plen)
        # pkt = data[5:].lstrip()
        # qDebug('%d, %s' % (plen, pkt))

        # self._tcpWrite(chan, pkt)
        
        return

    def _toxnetFileChunkRequest(self, friend_id, file_number, position, length):
        import random
        if random.randrange(0,9) == 1:
            qDebug('here')
            qDebug('%s, %d, %d, %d' % (friend_id, file_number, position, length))
        
        self_file_to_con_key = 'self_file_to_con_%d_%s' % (file_number, friend_id[0:64])
        con = self.cons[self_file_to_con_key]

        reqinfo = (friend_id, file_number, position, length)
        # qDebug(str(reqinfo))
        
        con.reqchunks.append(reqinfo)
        # qDebug('reqchunks len: %d' % len(chan.reqchunks))

        # if chan.sock.bytesAvailable() > 0: chan.sock.readyRead.emit()
        self._toxnetReadyWrite(con, friend_id, file_number)
        
        return
    
    def _toxnetFriendMessage(self, friendId, msg):
        qDebug(friendId)
        
        return

    def _toxnetReadyWrite(self, con, friend_id, file_number):

        belongs_chans = []
        for ck in self.chans:
            chan = self.chans[ck]
            if type(ck) == QTcpSocket and con == chan.con:  # 排除重复chan功能。
                belongs_chans.append(chan)
        

        candi_chans = []
        for chan in belongs_chans:
            if chan.sock.bytesAvailable() > 0: candi_chans.append(chan)
            elif chan.sock.state() != QTcpSocket.ConnectedState and chan.need_sent_close is True:
                pkt = {'chcli': chan.chanocli , 'chsrv': chan.chanosrv, 'type': 'CLOSE', 'data':''}
                jspkt = json.JSONEncoder().encode(pkt)
                fjspkt = '%1371s' % jspkt

                reqinfo = con.reqchunks.pop(0)
                bret = self.toxkit.fileSendChunk(con.peer, con.self_file_number, reqinfo[2], fjspkt)
                qDebug(str(bret))
                chan.need_sent_close = False
                return  # 因为这只是一个chunk包，所以只处理一个就消耗掉了，不再继续处理。

        
        if len(candi_chans) > 0:
            n = random.randrange(0, len(candi_chans))
            chan = candi_chans[n]
            chan.sock.readyRead.emit()

        return

    # @param data bytes | QByteArray
    def _toxnetWrite(self, chan, data):
        # cmdno = self._nextCmdno()
        # chan.cmdno = cmdno

        # extra = {'chano': chan.chano}
        # res = chan.rudp.buf_send_pkt(data, extra)
        
        return

    def _toxchanReadyRead(self):
        qDebug('here')
        udp = self.sender()
        chan = self.chans[udp]
        
        while True:
            opkt = udp.readPacket()
            if opkt is None: break
            self._tcpWrite(chan, opkt.data)
            
        return

    def _toxchanBytesWritten(self):
        udp = self.sender()
        chan =self.chans[udp]

        chan.sock.readyRead.emit()
        
        return

    def _toxchanDisconnected(self):
        qDebug('here')
        udp = self.sender()
        chan = self.chans[udp]
        sock = chan.sock
        
        # 清理资源
        if sock not in self.chans: qDebug('sock maybe already closed')
        else: self.chans.pop(sock)

        if udp not in self.chans: qDebug('udp maybe already closed')
        else: self.chans.pop(udp)

        chano = chan.chano
        if chano not in self.chans: qDebug('maybe already closed222')
        else: self.chans.pop(chano)

        qDebug('chans size: %d' % len(self.chans))
        
        return

    def _toxchanCanClose(self):
        udp = self.sender()
        chan = self.chans[udp]

        cmdno = self._nextCmdno()
        extra = {'cmd': 'close', 'chano': chan.chano, 'cmdno': cmdno, }
        res = chan.rudp.mkdiscon(extra)
        
        return

    def _toxchanPromiseCleanup(self, chan):
        sock = chan.sock
        chanosrv_key = 'chanosrv_%d' % chan.chanosrv

        promise_results = {
            'peer_close': chan.peer_close,
            # 'ctrl_close': chan.ctrl_close,
            'sock_close': chan.sock_close,
        }

        promise_result = True
        for pk in promise_results: promise_result = promise_result and promise_results[pk]

        if promise_result is True:
            qDebug('promise satisfied: %d<=>%d.' % (chan.chanocli, chan.chanosrv))
        else:
            qDebug('promise noooooot satisfied: %d<=>%d.' % (chan.chanocli, chan.chanosrv))
            qDebug(str(promise_results))
            return
        
        # if chan.peer_close is True and chan.ctrl_close is True: pass
        # else: return
        
        # 清理资源
        if sock not in self.chans: qDebug('sock maybe already closed')
        else: self.chans.pop(sock)

        if chanosrv_key not in self.chans: qDebug('chsrv already closed222')
        else: self.chans.pop(chanosrv_key)

        qDebug('chans size: %d' % len(self.chans))
        
        return

    
    def _onTcpConnected(self):
        qDebug('here')

        sock = self.sender()
        chan = self.chans[sock]

        # reply = {'cmd': 'connect', 'res': True, 'chano': chan.chano, 'cmdno': chan.cmdno, }
        #    self.toxkit.sendMessage(chan.con.peer, reply)
        return
            
    def _onTcpDisconnected(self):
        qDebug('here %d' % len(self.chans))
        sock = self.sender()

        if sock not in self.chans:
            qDebug('maybe already closed123')
            return

        chan = self.chans[sock]
        con = chan.con

        pkt = {'chcli': chan.chanocli , 'chsrv': chan.chanosrv, 'type': 'CLOSE', 'data':''}
        jspkt = json.JSONEncoder().encode(pkt)
        fjspkt = '%1371s' % jspkt

        if len(con.reqchunks) > 0:
            reqinfo = con.reqchunks.pop(0)
            bret = self.toxkit.fileSendChunk(con.peer, con.self_file_number, reqinfo[2], fjspkt)
            qDebug(str(bret))
            # chan.peer_close = True
        else:
            qDebug('no free reqchunk found')
            chan.need_sent_close = True
        

        # 这儿关闭的话就太早了
        chan.sock_close = True
        self._toxchanPromiseCleanup(chan)

        
        # chan = self.chans[sock]
        # chano = chan.chano

        # if chano not in self.chans:
        #     qDebug('maybe already closed222')
        #     self.chans.pop(sock)
        #     return

        # cmdno = self._nextCmdno()
        # msg = {'cmd': 'close', 'chano': chan.chano, 'cmdno': cmdno, }

        # extra = msg
        # chan.transport.closed = True
        # chan.rudp.startCheckClose()
        
        #jspkt = chan.rudp.mkdiscon(extra)
        #self.toxkit.sendMessage(chan.con.peer, jspkt)

        return

    def _onTcpError(self, error):
        sock = self.sender()
        qDebug('herhe %s' %  sock.errorString())
        return
    
        if sock not in self.chans:
            qDebug('maybe already closed123')
            return

        chan = self.chans[sock]
        con = chan.con

        pkt = {'chcli': chan.chanocli , 'chsrv': chan.chanosrv, 'type': 'CLOSE', 'data':''}
        jspkt = json.JSONEncoder().encode(pkt)
        fjspkt = '%1371s' % jspkt

        #if len(con.reqchunks) > 0:
        #    reqinfo = con.reqchunks.pop(0)
        #    bret = self.toxkit.fileSendChunk(con.peer, con.self_file_number, reqinfo[2], fjspkt)
        #    qDebug(str(bret))

        # self._toxchanPromiseCleanup(chan)

        # chan = self.chans[sock]
        # chano = chan.chano
        #if chano not in self.chans:
        #    qDebug('maybe already closed333')
        #    self.chans.pop(sock)
        #    return

        # cmdno = self._nextCmdno()
        # msg = {'cmd': 'close', 'chano': chan.chano, 'cmdno': cmdno,}
        
        # extra = msg
        # chan.transport.closed = True
        
        # chan.rudp.startCheckClose()
        # jspkt = chan.rudp.mkdiscon(extra)
        # self.toxkit.sendMessage(chan.con.peer, jspkt)

        return
    
    def _onTcpReadyRead(self):
        qDebug('here')
        sock = self.sender()
        chan = self.chans[sock]
        con = chan.con

        peekSize = 897  # 345  # 897  # 987时就有可能导致超长拆包发送
        # extra = {'chano': chan.chano}
        cnter = 0
        tlen = 0

        while sock.bytesAvailable() > 0 and len(con.reqchunks) > 0:
            bcc = sock.peek(peekSize)
            # reqinfo = con.reqchunks.pop(0)
            reqinfo = con.reqchunks[0]  # peek way
            qDebug(str(reqinfo))
            print(bcc[len(bcc)-50:])
            pkt = {'chcli': chan.chanocli, 'chsrv': chan.chanosrv, 'type': 'WRITE', 'data':''}
            rawpkt = QByteArray(bcc).toBase64().data().decode('utf8')
            pkt['data'] = rawpkt
            jspkt = json.JSONEncoder().encode(pkt)
            fullpkt = '%1371s' % (jspkt)
            bret = self.toxkit.fileSendChunk(con.peer, con.self_file_number, reqinfo[2], fullpkt)
            if bret is True:
                reqinfo = con.reqchunks.pop(0)
                bcc1 = sock.read(len(bcc))
                chan.rdlen += len(bcc)
                cnter += 1
                tlen += len(bcc)
            else: break


        # while sock.bytesAvailable() > 0:
        #     bcc = sock.peek(peekSize)
        #     res = chan.rudp.attemp_send(bcc, extra)
        #     if res is True:
        #         bcc1 = sock.read(len(bcc))
        #         chan.rdlen += len(bcc)
        #         cnter += 1
        #         tlen += len(bcc)
        #     else: break
                
        qDebug('XDR: sock->toxnet: %d/%d, %d' % (tlen, chan.rdlen, cnter))
        return

    
    def _tcpWrite(self, chan, data):
        qDebug('hrehe')
        sock = chan.sock

        if type(data) == str: data = data.encode('utf8')
        rawdata = QByteArray.fromBase64(data)
        # rawdata = chan.transport.decodeData(data)
        print(rawdata)
        n = sock.write(rawdata)
        chan.wrlen += n
        qDebug('XDR: toxnet->sock: %d/%d' % (n, chan.wrlen))
        
        return


def main():
    app = QCoreApplication(sys.argv)
    qtutil.pyctrl()

    config_file = './toxtun.ini'
    if len(sys.argv) == 2:
        config_file = sys.argv[1]
        if not os.path.exists(config_file):
            print('config file is not exists: %s' % config_file)
            help()
            sys.exit(1)
    elif len(sys.argv) == 1:
        pass
    else:
        print('provide a valid config file please')
        help()
        sys.exit(1)


    tunsrv = ToxTunFileSrv(config_file)
    tunsrv.start()
    
    app.exec_()
    return


if __name__ == '__main__': main()

