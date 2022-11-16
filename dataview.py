"""
super light n-d array viewer (like napari) to help debugging
author: jelmer cnossen 2021/2022
license: public domain
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSlider,QMenuBar
from PyQt5 import QtWidgets
import pyqtgraph as pg
import sys
import numpy as np
from PyQt5.QtWidgets import QApplication

def needs_qt(func):
    """
    Decorator to make sure QApplication is only instantiated once
    """
    def run(*args,**kwargs):
        app = QApplication.instance()
        appOwner = app is None
        if appOwner:
            app = QApplication(sys.argv)
        
        r = func(*args,**kwargs)
        
        if appOwner:
            del app
            
        return r
    return run


class ImageViewWindow(QtWidgets.QDialog):
    def __init__(self, img, event_listener, *args, **kwargs):
        super(ImageViewWindow, self).__init__(*args, **kwargs)
        
        self.setWindowTitle('Image Viewer')
        self.event_listener = event_listener
        
        self.menu=QMenuBar()
        ltop = QtWidgets.QHBoxLayout()
       
        layout = QtWidgets.QVBoxLayout()
        ltop.addLayout(layout)
        ltop.setMenuBar(self.menu)

        ctlLayout = QtWidgets.QGridLayout()

        sliders=[]        
        for i in range( len(img.shape)-2 ):
            slider = QSlider(Qt.Horizontal)
            slider.setFocusPolicy(Qt.StrongFocus)
            slider.setTickPosition(QSlider.TicksBothSides)
            slider.setTickInterval(10)
            slider.setSingleStep(1)
            slider.setMaximum(img.shape[i]-1)
            slider.valueChanged.connect(self.sliderChange)
            layout.addWidget(slider)#, 0, 0)
            sliders.append(slider)
        self.sliders=sliders

        self.info = QtWidgets.QLabel()
        ctlLayout.addWidget(self.info, 0, 2, Qt.AlignLeft)

        layout.addLayout(ctlLayout)
        view = pg.ImageView()
        layout.addWidget(view)
        self.view = view
        self.imv = view.imageItem
        self.imv.scene().sigMouseClicked.connect(self.mouseClicked)    

        self.setLayout(ltop)

        self.imv.setImage(img)
        self.data = img
        self.sliderChange()

    def mouseClicked(self, event):
        pos = event.scenePos() # event.pos() depends on which item is clicked

        image_pos = self.imv.mapFromDevice(pos)
        #print(f'device pos: {pos}, image pos: {image_pos}')

        if self.event_listener is not None:
            self.event_listener('click', self, event, image_pos)

    def sliderChange(self):
        d = self.data
        ix=[]
        for s in self.sliders:
            ix.append(s.value())
            d=d[s.value()]
        self.imv.setImage(d.T)
        self.info.setText("["+','.join([str(i) for i in ix])+']')

    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        #self.closeCamera()
        ...

        
    def closeEvent(self, event):
        #print('close event')
        #self.closeCamera()
        event.accept()



@needs_qt
def view_images(img, title=None, modal=True, parent=None,event_listener=None):
    if getattr(img, "cpu", None): # convert torch tensors without importing torch
        img = img.cpu().numpy()
    w = ImageViewWindow(np.array(img), parent=parent, event_listener=event_listener)
    w.setModal(modal)
    if title is not None:
        w.setWindowTitle(title)
    if modal:
        w.exec_()
    else:
        w.show()
    return w


if __name__ == '__main__':
    img = np.random.uniform(0, 100, size=(20,5,200,200)).astype(np.uint8)

    def click_handler(event, wnd : ImageViewWindow, ev, pos):
        w = 10
        wnd.view.addItem(pg.RectROI((pos.x() - w/2, pos.y()-w/2), (w,w)))
    
    v = view_images(img, event_listener = click_handler)

    


