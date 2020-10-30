import numpy as np

class Search:
    def __init__(self, label_matrix):
        self.label_matrix = label_matrix
        self.label_nums = len(label_matrix[0])
        self.max_pos, self.max_label = self.searchMax()

    def comput_direction(self, labels):
        self.direction = 0
        for i in range(len(labels) - 1):
            if labels[i + 1] > labels[i]:
                self.direction += 1
            elif labels[i + 1] < labels[i]:
                self.direction -= 1
        if self.direction >= 0:
            return labels
        else:
            return labels[::-1]

    def searchMax(self):
        '''
        :return: max_pos, max_label 起始位置的横纵坐标
        '''
        thresh_matrix = self.label_matrix.copy()
        # thresh_matrix[thresh_matrix < 0.6] = 0.0 # 剔除小值
        # max_pos, max_label = np.unravel_index(np.argmax(thresh_matrix), thresh_matrix.shape) # 直接找出概率最大的一个
        tmp_labels = thresh_matrix.argmax(axis=-1) # 单个序列对应类别值
        tmp_labels = self.comput_direction(tmp_labels)
        label_count = np.bincount(tmp_labels) # 各类别总数
        max_label = np.argmax(label_count) # 数量最多的类别
        max_pos = np.argmax(thresh_matrix[:,max_label]) # 属于最多类别且概率最大的一例
        return max_pos, max_label

    def forward(self, label, index):
        label = self.label_nums - 1 - label
        index = len(self.label_matrix) - 1 - index
        tran_matrix = self.label_matrix.copy()
        tran_matrix = tran_matrix[::-1, ::-1]
        path = []
        for i in range(index, len(tran_matrix)):

            if label > 0:
                curr_label = int(np.argmax(tran_matrix[i][label: label + 4]) + label)
                path.extend([self.label_nums - 1 - curr_label])
                label = curr_label
            else:
                curr_label = int(np.argmax(tran_matrix[i][label: label + 2]) + label)
                path.extend([self.label_nums - 1 - curr_label])
                label = curr_label
        return path[::-1]

    def backward(self, label, index):
        path = []
        for i in range(index, len(self.label_matrix)):

            if label > 0:
                curr_label = int(np.argmax(self.label_matrix[i][label: label + 4]) + label)
                path.extend([curr_label])
                label = curr_label
            else:
                curr_label = int(np.argmax(self.label_matrix[i][label: label + 2]) + label)
                path.extend([curr_label])
                label = curr_label
        return path

    def searchPath(self):
        if self.direction < 0:
            self.label_matrix = self.label_matrix[::-1]
        path = self.forward(int(self.max_label), self.max_pos - 1)
        path.extend([int(self.max_label)])
        path.extend(self.backward(int(self.max_label), self.max_pos + 1))
        return path

if __name__ == '__main__':
    from confusion_matrix import confusion_matrix, plot_confusion_matrix
    import matplotlib.pyplot as plt

    labels = ['脑部', '脑部鼻咽部', '鼻咽部', '鼻咽部颈部', '颈部', '颈部胸部', '胸部', '胸腹部',
              '腹部', '腹部盆腔', '盆腔', '盆腔下肢', '下肢']
    # label_matrix = np.array([[.7, .2, .3, .4, .5, .2, .1],
    #                          [.2, .6, .3, .1, .7, .2, .1],
    #                          [.1, .1, .8, .5, .5, .2, .1],
    #                          [.2, .9, .8, .2, .5, .2, .1],
    #                          [.2, .5, .7, .6, .5, .9, .1],
    #                          [.2, .4, .6, .4, .5, .2, .9]])
    # print(label_matrix[::-1, ::-1])
    prediction_label_matrix = np.load("../predictions.npy")
    true_label_matrix = np.load("../label_lists.npy")
    predictions = np.array([])
    truelabel = np.array([])
    for prediction_label, true_label in zip(prediction_label_matrix, true_label_matrix):
        prediction_label = np.array(prediction_label)
        print(true_label)
        isolated_prediction = list(prediction_label.argmax(axis=-1))
        print(list(isolated_prediction))
        s = Search(prediction_label)
        path = s.searchPath()
        print(path)
        print('')
        predictions = np.concatenate((predictions, np.array(path)), axis=0)
        truelabel = np.concatenate((truelabel, np.array(true_label)), axis=0)
    conf_mat = confusion_matrix(y_true=truelabel, y_pred=predictions)
    plt.figure()
    plot_confusion_matrix(conf_mat, normalize=False, target_names=labels, title='Confusion Matrix')