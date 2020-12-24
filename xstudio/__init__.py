import os
import clr
import sys
#import ipdb
import System
from typing import List,Tuple,Dict,Union

#导入.net基础库
from System.IO import FileStream,FileMode,FileAccess,FileShare
from System.Runtime.Serialization.Formatters.Binary import BinaryFormatter
#导入xs相关dll
clr.AddReference(os.path.split(os.path.abspath(__file__))[0]+"\\SingingTool.Model.dll")

class Svipnote():
    '''
    svip音符类    
    start:起点，480为一拍，int
    length:长度，480为一拍，int
    notenum:音高，与midi相同，即C4为60，音高越高，数值越大，int
    lyric:歌词汉字，str
    pronouncing:如果歌词拼音被修改过则为拼音，否则为空字符串，str
    '''
    def __init__(self,
                 start:int,
                 length:int,
                 notenum:int,
                 lyric:str,
                 pronouncing:str="",):
        self.start=start
        self.length=length
        self.notenum=notenum
        self.lyric=lyric
        self.pronouncing=pronouncing

    def __str__(self):
        return "  Svipnote {} {} {} {} {}".format(self.start,
            self.length,
            self.notenum,
            self.lyric,
            self.pronouncing)

class Sviptrack():
    '''
    svip音轨类
    name:音轨名，str
    singer:歌手编号，str
    note:音符列表，List[Svipnote]
    volume:音量，float，[0,2]
    balance:左右声道平衡，float，[-1,1]
    mute:静音，bool
    solo:独奏，bool
    reverb:混响类型，int
    '''
    def __init__(self,
                 name:str="",
                 singer:str="F802",
                 note:List[Svipnote]=[],
                 volume:float=0.7,
                 balance:float=0.0,
                 mute:bool=False,
                 solo:bool=False,
                 reverb:int=7,):
        if(note==[]):
            note=[]
        self.name=name
        self.singer=singer
        self.note=note
        self.volume=volume
        self.balance=balance
        self.mute=mute
        self.solo=solo
        self.reverb=reverb

    def __str__(self):
        return " Sviptrack {} {}\n".format(self.name,self.singer)+"\n".join((str(i) for i in self.note))

    def to_midi_track(self):
        '''
        将svip区段对象转换为mido.MidiTrack对象（暂不支持歌词）
        '''
        import mido
        track=mido.MidiTrack()
        time=0
        #track.append(mido.MetaMessage('track_name',name=bytes(self.name,encoding="utf8"),time=0))
        for note in self.note:
            #track.append(mido.MetaMessage('lyrics',text=bytes(note.lyric,encoding="utf8"),time=(note.start-time)))
            track.append(mido.Message('note_on', note=note.notenum,velocity=64,time=0))
            track.append(mido.Message('note_off',note=note.notenum,velocity=64,time=note.length))
            time=note.start+note.length
        track.append(mido.MetaMessage('end_of_track'))
        return track

class Svipfile():
    '''
    svip文件类
    tempo:曲速标记列表，
        曲速标记：(位置,曲速)
    beats:节拍标记列表
        节拍标记：(小节数位置,每小节拍数,x分音符为1拍(只能为1,2,4,8,16,32))
    track:音轨列表
    inst:伴奏音轨列表
    '''
    def __init__(self,
                 tempo:List[tuple]=[],
                 beats:List[tuple]=[],
                 track:List[Sviptrack]=[]):
        self.tempo=tempo
        self.beats=beats
        self.track=track

    def __str__(self):
        return "Svipfile\n"+"\n".join((str(i) for i in self.track))

    def to_midi_file(self):
        '''
        将svip文件对象转换为mid文件与mido.MidiFile对象（暂不支持歌词）
        '''
        import mido
        mid = mido.MidiFile()
        """
        #控制轨
        ctrltrack=mido.MidiTrack()
        ctrltrack.append(mido.MetaMessage('track_name',name='Control',time=0))
        tick=0
        for i in self.tempo:
            ctrltrack.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(i[1]),time=i[0]-tick))
            tick=i[0]
        mid.tracks.append(ctrltrack)
        """
        for i in self.track:
            mid.tracks.append(i.to_midi_track())
        return mid

def parsenote(noteobject)->Svipnote:
    #解析音符对象
    return Svipnote(start=noteobject.StartPos,
                    length=noteobject.WidthPos,
                    notenum=noteobject.KeyIndex,
                    lyric=noteobject.Lyric,
                    pronouncing=noteobject.Pronouncing)
    pass

def parsetrack(trackobject)->Sviptrack:
    #解析音轨对象
    return Sviptrack(name=trackobject.Name,
                     singer=trackobject.AISingerId,
                     note=[parsenote(i) for i in trackobject.NoteList.GetEnumerator()],
                     volume=trackobject.Volume,
                     balance=trackobject.Pan,
                     mute=trackobject.Mute,
                     solo=trackobject.Solo,
                     reverb=trackobject.ReverbPreset,)

def parsefile(fileobject)->Svipfile:
    #解析文件对象
    track=[]
    for i in fileobject.TrackList:
        if(i.ToString()=="SingingTool.Model.SingingTrack"):#过滤伴奏音轨，保留合成音轨
            track.append(parsetrack(i))
    return Svipfile(track=track)

def opensvip(filename:str):
    """
    打开svip文件，返回Svipfile对象
    """
    serializer = BinaryFormatter()
    reader = FileStream(filename, FileMode.Open, FileAccess.Read)
    for i in range(11):
        reader.ReadByte()
    data = serializer.Deserialize(reader)
    reader.Close()
    return parsefile(data)

    #for p in nlpy:
    #    print(p.StartPos,p.WidthPos,p.Lyric,p.KeyIndex)
    #for p in data.GetType().GetProperties():print(p.Name,p.GetValue(data))#获取data的全部属性和值
    #for p in data.GetType().GetMethods():print(p,p.GetParameters)#获取data的全部方法和参数

def main():
    s=opensvip(r"C:/users/lin/desktop/2.svip")
    s.to_midi_file().save(r"C:/users/lin/desktop/2.mid")

if __name__=="__main__":
    main()

"""
文件对象 SingingTool.Model.AppModel
ProjectFilePath
ProjectFileStream None
TempoList SingingTool.Library.SerialOverlapableItemList`1[SingingTool.Model.SingingGeneralConcept.SongTempo]
ReadOnlyTempoList SingingTool.Library.SerialOverlapableItemList`1[SingingTool.Model.SingingGeneralConcept.SongTempo]
BeatList SingingTool.Library.SerialOverlapableItemList`1[SingingTool.Model.SingingGeneralConcept.SongBeat]
ReadOnlyBeatList SingingTool.Library.SerialOverlapableItemList`1[SingingTool.Model.SingingGeneralConcept.SongBeat]
TrackList [<SingingTool.Model.SingingTrack object at 0x0000027C63186708>] #音轨列表
ReadOnlyTrackList [<SingingTool.Model.SingingTrack object at 0x0000027C63182788>]
QuantizeValue 16
IsTriplet False
QuantizeLengthInPos 120
IsNumerialKeyName True
FirstNumerialKeyNameAtIndex 0
"""

"""
音轨对象 SingingTool.Model.SingingTrack
AISingerId F802
NoteList SingingTool.Library.SerialOverlapableItemList`1[SingingTool.Model.Note] #音符列表
ReadOnlyNoteList SingingTool.Library.SerialOverlapableItemList`1[SingingTool.Model.Note]
Selected False
NeedRefreshBaseMetadataFlag True
IsFetchingBaseMetadata False
EditedPitchLine SingingTool.Model.Line.LineParam
ReverbPreset 7
Volume 0.7
Pan 0.0
Mute False
Solo False
Name 演唱轨
"""

"""
列表容器 SingingTool.Library.SerialOverlapableItemList`1 拥有以下方法
IsOverlapedItemsExists
GetOverlapedItemsInside
GetOverlapedItems
InsertItemInOrder
RemoveItem
get_Count #内容数量
get_Item #获取指定位置的音符
IndexOf
InsertListItemsInOrder
RemoveListItems
RemoveAllItems
IsElementExists
GetEnumerator #获取一个迭代器，它返回音符
Equals
GetHashCode
GetType
ToString
"""

"""
音符对象 SingingTool.Model.Note
StartPos 17520
ActualStartPos 17520
WidthPos 240
KeyIndex 67
Lyric 曾
Pronouncing
HeadTag 0
Overlaped False
Selected False
LengthValidateTag 0
NotePhoneInfo None
ReadOnlyNotePhoneInfo None
"""