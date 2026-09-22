"""学习笔记：模型只描述“输入如何变成输出”，不负责训练。"""

from torch import nn


class DigitMLP(nn.Module):
    """识别 0～9 的小型全连接网络（MLP），默认结构为 784 → 128 → 10。"""

    def __init__(self, hidden_size: int = 128):
        # nn.Module 帮我们管理各层和可学习参数，先初始化它。
        super().__init__()
        self.layers = nn.Sequential(
            # 每张图片铺平成 784 个数；默认从第 1 维开始展平，保留批次维。
            # [B, 1, 28, 28] → [B, 784]，B 表示这批图片的数量。
            nn.Flatten(),
            # 每个隐藏单元对 784 个像素加权求和，再加偏置。
            # 权重和偏置是要学习的参数，而 128 是我们预先选择的结构大小。
            nn.Linear(784, hidden_size),
            # ReLU 把负数变成 0，保留非负数，形状仍为 [B, 128]。
            # 这种非线性让多层网络能表达比单次线性变换更复杂的关系。
            nn.ReLU(),
            # 输出 [B, 10]，每一行是某张图片对数字 0～9 的十个分数。
            nn.Linear(hidden_size, 10),
        )

    def forward(self, images):
        # 调用 model(images) 时，PyTorch 会执行这里的前向传播。
        # 输出称为 logits，可以为负数，也不要求加起来等于 1。
        # CrossEntropyLoss 直接接收这些分数，因此这里不额外加 softmax。
        return self.layers(images)
