import torch
import torch.nn as nn
import torch.nn.functional as F

def weights_init(w):
    classname = w.__class__.__name__
    if classname.find('conv') != -1:
        nn.init.normal_(w.weight.data, 0.0, 0.02)
    elif classname.find('bn') != -1:
        nn.init.normal_(w.weight.data, 1.0, 0.02)
        nn.init.constant_(w.bias.data, 0)

# Define the Generator Network
class Generator(nn.Module):
    def __init__(self, params):
        super().__init__()

        self.label_embed = nn.Embedding(params['vocab_size'], params['embedding_size'])

        # Input is the latent vector Z.
        self.tconv1_1 = nn.ConvTranspose2d(params['nz'], params['ngf']*8, 
                                           kernel_size=4, stride=1, 
                                           padding=0, bias=False)
        self.tconv1_2 = nn.ConvTranspose2d(params['n_conditions']*params['embedding_size'],
                                           params['ngf']*8, kernel_size=4, stride=1, 
                                           padding=0, bias=False)
        
        self.bn1_1 = nn.BatchNorm2d(params['ngf']*8)
        self.bn1_2 = nn.BatchNorm2d(params['ngf']*8)

        # Input Dimension: (ngf*8) x 4 x 4
        self.tconv2 = nn.ConvTranspose2d(params['ngf']*8, params['ngf']*4,
            4, 2, 1, bias=False)
        self.bn2 = nn.BatchNorm2d(params['ngf']*4)

        # Input Dimension: (ngf*4) x 8 x 8
        self.tconv3 = nn.ConvTranspose2d(params['ngf']*4, params['ngf']*2,
            4, 2, 1, bias=False)
        self.bn3 = nn.BatchNorm2d(params['ngf']*2)

        # Input Dimension: (ngf*2) x 16 x 16
        self.tconv4 = nn.ConvTranspose2d(params['ngf']*2, params['ngf'],
            4, 2, 1, bias=False)
        self.bn4 = nn.BatchNorm2d(params['ngf'])

        # Input Dimension: (ngf) * 32 * 32
        self.tconv5 = nn.ConvTranspose2d(params['ngf'], params['nc'],
            4, 2, 1, bias=False)
        #Output Dimension: (nc) x 64 x 64

    def forward(self, x, labels):
        batch_size, _ = labels.size()
        z = x

        labels_embed = self.label_embed(labels)
        #labels_embed = labels_embed.view(batch_size, 1, 1, -1)
        #labels_embed = torch.transpose(labels_embed, 1, 3)
        
        #input_encoding = torch.cat((x, labels_embed), dim=1)

        x = F.relu(self.bn1_1(self.tconv1_1(x)))
        y = F.relu(self.bn1_2(self.tconv1_2(labels_embed)))

        x = torch.cat((x, y), dim=1)

        x = F.relu(self.bn2(self.tconv2(x)))
        x = F.relu(self.bn3(self.tconv3(x)))
        x = F.relu(self.bn4(self.tconv4(x)))

        x = F.tanh(self.tconv5(x))

        return x

# Define the Discriminator Network
class Discriminator(nn.Module):
    def __init__(self, params):
        super().__init__()

        self.label_embed = nn.Embedding(params['vocab_size'], params['embedding_size']) 

        # Input Dimension: (nc) x 64 x 64
        self.conv1_1 = nn.Conv2d(params['nc'], params['ndf'],
            4, 2, 1, bias=False)

        self.conv1_2 = nn.Conv2d(params['embedding_size'] * params['n_conditions'], params['ndf'],
            4, 2, 1, bias=False)

        # Input Dimension: (ndf) x 32 x 32
        self.conv2 = nn.Conv2d(params['ndf'], params['ndf']*2,
            4, 2, 1, bias=False)
        self.bn2 = nn.BatchNorm2d(params['ndf']*2)

        # Input Dimension: (ndf*2) x 16 x 16
        self.conv3 = nn.Conv2d(params['ndf']*2, params['ndf']*4,
            4, 2, 1, bias=False)
        self.bn3 = nn.BatchNorm2d(params['ndf']*4)

        # Input Dimension: (ndf*4) x 8 x 8
        self.conv4 = nn.Conv2d(params['ndf']*4, params['ndf']*8,
            4, 2, 1, bias=False)
        self.bn4 = nn.BatchNorm2d(params['ndf']*8)

        # Input Dimension: (ndf*8) x 4 x 4
        self.conv5 = nn.Conv2d(params['ndf']*8, 1, 4, 1, 0, bias=False)

    def forward(self, x, labels):
        batch_size, _ = labels.size()
        img = x

        labels_embed = self.label_embed(labels)
        labels_embed_fill = labels_embed.repeat(1, 1, params['imsize'], params['imsize'])

        x = F.leaky_relu(self.conv1_1(x), 0.2, True)
        y = F.leaky_relu(self.conv1_2(labels_embed_fill), 0.2, True)

        x = torch.cat((x, y), dim=1)

        x = F.leaky_relu(self.bn2(self.conv2(x)), 0.2, True)
        x = F.leaky_relu(self.bn3(self.conv3(x)), 0.2, True)
        x = F.leaky_relu(self.bn4(self.conv4(x)), 0.2, True)

        x = F.sigmoid(self.conv5(x))

        return x