from pydicom.multival import MultiValue
from scipy.ndimage import zoom
import pydicom as dicom
from PIL import Image
import numpy as np
import os
os.chdir('./')

BODY = ["脑部", "脑部鼻咽部", "鼻咽部", "鼻咽部颈部", "颈部", "颈部胸部", "胸部", "胸部腹部", "腹部", "腹部盆腔", "盆腔", "盆腔下肢", "下肢"]
HU_MAX = 1024.
HU_MIN = -1024.
ZAOYING = ["平扫", "动脉期", "门静脉期", "静脉期", "延迟期"]


class Slice():
    """
    * Slice
        * attributes
            * PatientID
            * studyID
            * patientName
            * patientBirthDate
            * patientSex
            * Series Instance UID: 序列号
            * SOP Instance UID: 切片序列号
            * InstanceNumber: 切片编号
            * Slice Thickness: 切片厚度
            * Pixel Spacing: 切片"像素"点间距离
            * Slice Location:切片在学列中位置
            * SamplesPerPixel: assert 1
            * Window Center:窗位
            * Window Width:窗宽
            * Rescale Intercept:[Dicom图像值与HU值](https://www.jianshu.com/p/f98635abac65)
            * Rescale Slope:
            * array2D: 切片数值, numpy.array
            * standard pixel spacing:[1,1,1] in mm
            * body parts
        * operations
            * unifySpacing
            * unifyPixelValue
            * unifySpacingAndPixelValue
            * saveWithWindow
    """

    def __init__(self, dicomFilePath):
        slice = dicom.read_file(dicomFilePath)
        self.dicomSlicePath = dicomFilePath
        self.patientID = slice.PatientID
        self.patientName = slice.PatientName
        self.patientBirthDate = slice.PatientBirthDate
        self.patientSex = slice.PatientSex
        self.studyID = slice.StudyID
        self.seriesInstanceUID = slice.SeriesInstanceUID
        self.sopInstanceUID = slice.SOPInstanceUID
        self.instanceNumber = slice.InstanceNumber
        self.sliceThickness = float(slice.SliceThickness) if hasattr(slice, "SliceThickness") else 0.
        if isinstance(slice.PixelSpacing, MultiValue):
            self.pixelSpacing = np.array([float(space) for space in slice.PixelSpacing])
        else:
            self.pixelSpacing = np.array([float(slice.PixelSpacing), float(slice.PixelSpacing)])
        self.sliceLocation = float(slice.ImagePositionPatient[-1]) if hasattr(slice, "ImagePositionPatient") else -1.
        # self.samplesPerPixel = int(slice.SamplesPerPixel)
        # assert self.samplesPerPixel == 1
        self.windowCenter = float(slice.WindowCenter[0]) if isinstance(slice.WindowCenter, MultiValue) else float(
            slice.WindowCenter)
        self.windowWidth = float(slice.WindowWidth[0]) if isinstance(slice.WindowWidth, MultiValue) else float(
            slice.WindowWidth)
        self.rescaleIntercept = float(slice.RescaleIntercept) if hasattr(slice, "RescaleIntercept") else -1024.
        self.rescaleSlope = float(slice.RescaleSlope) if hasattr(slice, "RescaleSlope") else 1.
        self.array2D = slice.pixel_array.astype(float) * self.rescaleSlope + self.rescaleIntercept
        self.standardPixelSpacing = [1., 1.]
        self.bodyParts = []
        self.zaoying = ""

    @staticmethod
    def unifySpacing(array2D, pixelSpacing):
        arr = zoom(array2D, pixelSpacing, order=3, mode="nearest")
        assert id(arr) != id(array2D)
        return arr

    @staticmethod
    def unifyPixelValue(array2D):
        arr = (array2D - HU_MIN) / (HU_MAX - HU_MIN)
        arr[arr < 0.] = 0.
        arr[arr > 1.] = 1.
        assert id(arr) != id(array2D)
        return arr

    def unifySpacingAndPixelValue(self):
        return self.unifyPixelValue(self.unifySpacing(array2D=self.array2D, pixelSpacing=self.pixelSpacing))

    def saveWithWindow(self, toFile):
        arr = self.array2D.copy()
        lower = self.windowCenter - self.windowWidth / 2
        upper = self.windowCenter - self.windowWidth / 2
        arr = (arr - lower) / self.windowWidth * 255.
        arr[arr < 0.] = 0.
        arr[arr > 255.] = 255.
        image = Image.fromarray(arr.astype(np.uint8))
        image.save(toFile)

class Series():
    """
    * Series
        * attributes
            * series
            * Series Instance UID
            * pixel Spacing
        * operations
            * unifySpacing
            * unifyPixelValue
            * stack
            * sort
            * append
    """

    def __init__(self, slice):
        assert isinstance(slice, Slice)
        self.series = [slice]
        self.seriesInstanceUID = slice.seriesInstanceUID
        self.zaoying = slice.zaoying
        self.pixelSpacing = np.concatenate([slice.pixelSpacing, np.array([slice.sliceThickness])])  # x, y, z


    def append(self, slice):
        assert isinstance(slice, Slice)
        assert slice.zaoying == self.zaoying
        self.series.append(slice)

    @staticmethod
    def unifyPixelValue(array3D):
        arr = (array3D - HU_MIN) / (HU_MAX - HU_MIN)
        arr[arr < 0.] = 0.
        arr[arr > 1.] = 1.
        assert id(arr) != id(array3D)
        return arr

    @staticmethod
    def unifyspacing(array3D, pixelSpacing):
        arr = zoom(array3D, pixelSpacing, order=3, mode="nearest")
        assert id(arr) != id(array3D)
        return arr

    @staticmethod
    def sortBySliceLocation(slices):
        return sorted(slices, key=lambda slice: slice.sopInstanceUID, reverse=False)

    @staticmethod
    def sortBySliceSOPInstanceUID(slices):
        new_slices = []
        for slice in slices:
            new_slices.append([slice, int(str(slice.sopInstanceUID).replace('.', ''))])
        new_slices = sorted(new_slices, key=lambda slice: slice[1], reverse=False)
        res_slices = []
        for slice in new_slices:
            res_slices.append(slice[0])
        return res_slices

    @staticmethod
    def sortByInstanceNumber(slices):
        return sorted(slices, key=lambda slice: slice.instanceNumber, reverse=False)

    @staticmethod
    def multSort(slices):
        new_slices = []
        for slice in slices:
            new_slices.append([slice, int(str(slice.sopInstanceUID).split('.')[-2]), int(str(slice.sopInstanceUID).split('.')[-1])])
        new_slices = sorted(new_slices, key=lambda slice: (-slice[1], slice[2], slice[0].sliceLocation), reverse=False)
        res_slices = []
        for slice in new_slices:
            res_slices.append(slice[0])
        return res_slices

    @staticmethod
    def stack(slices):
        assert all([slice.array2D.shape == slices[0].array2D.shape for slice in slices])
        return np.stack([slice.array2D for slice in slices])

    def selectBodyPart(self, bodyPart, stack=True):
        assert all([slice.bodyParts for slice in self.series])
        bodyPartsSlices = [slice for slice in self.series if bodyPart in slice.bodyParts]
        bodyPartsSlices = self.sortBySliceLocation(bodyPartsSlices)
        return self.stack(bodyPartsSlices) if stack else bodyPartsSlices


def groupSlices(dicomFiles):
    seriesDict = {}
    dicomFilesDir = dicomFiles
    dicomFiles = os.listdir(dicomFiles)
    for dicomFile in dicomFiles:
        dicomFile = os.path.join(dicomFilesDir, dicomFile)
        slice = Slice(dicomFilePath=dicomFile)
        if slice.seriesInstanceUID in seriesDict:
            seriesDict[slice.seriesInstanceUID].append(slice)
        else:
            seriesDict[slice.seriesInstanceUID] = Series(slice=slice)
    return seriesDict


