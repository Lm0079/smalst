'''
CNN building blocks.
Taken from https://github.com/shubhtuls/factored3d/
'''
from __future__ import division
from __future__ import print_function
import torch
import torch.nn as nn
import math

class Flatten(nn.Module):
    def forward(self, x):
        return x.view(x.size()[0], -1)

class Unsqueeze(nn.Module):
    def __init__(self, dim):
        super(Unsqueeze, self).__init__()
        self.dim = dim

    def forward(self, x):
        return x.unsqueeze(self.dim)

## fc layers
def fc(norm_type, nc_inp, nc_out):
    if norm_type == 'batch':
        return nn.Sequential(
            nn.Linear(nc_inp, nc_out, bias=True),
            nn.BatchNorm1d(nc_out),
            nn.LeakyReLU(0.2,inplace=True)
        )
    else:
        return nn.Sequential(
            nn.Linear(nc_inp, nc_out),
            nn.LeakyReLU(0.1,inplace=True)
        )

def fc_stack(nc_inp, nc_out, nlayers, norm_type='batch'):
    modules = []
    for l in range(nlayers):
        modules.append(fc(norm_type, nc_inp, nc_out))
        nc_inp = nc_out
    encoder = nn.Sequential(*modules)
    net_init(encoder)
    return encoder

def fc_stack_dropout(nc_inp, nc_out, nlayers): 
    modules = []
    modules.append(nn.Linear(nc_inp, 1024, bias=True))
    modules.append(nn.ReLU())
    modules.append(nn.Dropout())
    modules.append(nn.Linear(1024, 1024, bias=True))
    modules.append(nn.ReLU())
    modules.append(nn.Dropout())
    modules.append(nn.Linear(1024, nc_out, bias=True))

    encoder = nn.Sequential(*modules)
    net_init(encoder)
    nl = 1
    for m in encoder.modules():
        if isinstance(m, nn.Linear):
            if nl == nlayers:
                torch.nn.init.xavier_normal(m.weight, gain=0.01)
            else:
                torch.nn.init.xavier_normal(m.weight)
            if m.bias is not None:
                m.bias.data.zero_()
            nl += 1

    return encoder

## 2D convolution layers
def conv2d(norm_type, in_planes, out_planes, kernel_size=3, stride=1, num_groups=2):
    if norm_type == 'batch':
        return nn.Sequential(
            nn.Conv2d(in_planes, out_planes, kernel_size=kernel_size, stride=stride, padding=(kernel_size-1)//2, bias=True),
            nn.BatchNorm2d(out_planes),
            nn.LeakyReLU(0.2,inplace=True)
        )
    elif norm_type == 'group':
        return nn.Sequential(
            nn.Conv2d(in_planes, out_planes, kernel_size=kernel_size, stride=stride, padding=(kernel_size-1)//2, bias=True),
            nn.GroupNorm(num_groups, out_planes),
            nn.LeakyReLU(0.2,inplace=True)
        )
    else:
        return nn.Sequential(
            nn.Conv2d(in_planes, out_planes, kernel_size=kernel_size, stride=stride, padding=(kernel_size-1)//2, bias=True),
            nn.LeakyReLU(0.2,inplace=True)
        )


def deconv2d(in_planes, out_planes):
    return nn.Sequential(
        nn.ConvTranspose2d(in_planes, out_planes, kernel_size=4, stride=2, padding=1, bias=True),
        nn.LeakyReLU(0.2,inplace=True)
    )


def upconv2d(in_planes, out_planes, mode='bilinear'):
    if mode == 'nearest':
        print('Using NN upsample!!')
    upconv = nn.Sequential(
        nn.Upsample(scale_factor=2, mode=mode,align_corners = True),
        nn.ReflectionPad2d(1),
        nn.Conv2d(in_planes, out_planes, kernel_size=3, stride=1, padding=0),
        nn.LeakyReLU(0.2,inplace=True)
    )
    return upconv


def decoder2d(nlayers, nz_shape, nc_input, norm_type='batch', nc_final=1, nc_min=8, nc_step=1, init_fc=True, use_deconv=False, upconv_mode='bilinear', num_groups=2):
    ''' Simple 3D encoder with nlayers.
    
    Args:
        nlayers: number of decoder layers
        nz_shape: number of bottleneck
        nc_input: number of channels to start upconvolution from
        use_bn: whether to use batch_norm
        nc_final: number of output channels
        nc_min: number of min channels
        nc_step: double number of channels every nc_step layers
        init_fc: initial features are not spatial, use an fc & unsqueezing to make them 3D
    '''
    modules = []
    if init_fc:
        modules.append(fc('batch', nz_shape, nc_input))
        for d in range(3):
            modules.append(Unsqueeze(2))
    nc_output = nc_input
    for nl in range(nlayers):
        if (nl % nc_step==0) and (nc_output//2 >= nc_min):
            nc_output = nc_output//2
        if use_deconv:
            print('Using deconv decoder!')
            modules.append(deconv2d(nc_input, nc_output))
            nc_input = nc_output
            modules.append(conv2d(norm_type, nc_input, nc_output, num_groups=num_groups//2))
        else:
            modules.append(upconv2d(nc_input, nc_output, mode=upconv_mode))
            nc_input = nc_output
            modules.append(conv2d(norm_type, nc_input, nc_output, num_groups=num_groups//2))

    modules.append(nn.Conv2d(nc_output, nc_final, kernel_size=3, stride=1, padding=1, bias=True))
    decoder = nn.Sequential(*modules)
    net_init(decoder)
    return decoder


## 3D convolution layers
def conv3d(norm_type, in_planes, out_planes, kernel_size=3, stride=1, num_groups=2):
    if norm_type == 'batch':
        return nn.Sequential(
            nn.Conv3d(in_planes, out_planes, kernel_size=kernel_size, stride=stride, padding=(kernel_size-1)//2, bias=True),
            nn.BatchNorm3d(out_planes),
            nn.LeakyReLU(0.2,inplace=True)
        )
    elif norm_type == 'group':
        return nn.Sequential(
            nn.Conv3d(in_planes, out_planes, kernel_size=kernel_size, stride=stride, padding=(kernel_size-1)//2, bias=True),
            nn.GroupNorm(num_groups, out_planes),
            nn.LeakyReLU(0.2,inplace=True)
        )
    else:
        return nn.Sequential(
            nn.Conv3d(in_planes, out_planes, kernel_size=kernel_size, stride=stride, padding=(kernel_size-1)//2, bias=True),
            nn.LeakyReLU(0.2,inplace=True)
        )


def deconv3d(norm_type, in_planes, out_planes, num_groups=2):
    if norm_type == 'batch':
        return nn.Sequential(
            nn.ConvTranspose3d(in_planes, out_planes, kernel_size=4, stride=2, padding=1, bias=True),
            nn.BatchNorm3d(out_planes),
            nn.LeakyReLU(0.2,inplace=True)
        )
    elif norm_type == 'group':
        return nn.Sequential(
            nn.ConvTranspose3d(in_planes, out_planes, kernel_size=4, stride=2, padding=1, bias=True),
            nn.GroupNorm(num_groups, out_planes),
            nn.LeakyReLU(0.2,inplace=True)
        )
    else:        
        return nn.Sequential(
            nn.ConvTranspose3d(in_planes, out_planes, kernel_size=4, stride=2, padding=1, bias=True),
            nn.LeakyReLU(0.2,inplace=True)
        )


## 3D Network Modules
def encoder3d(nlayers, norm_type='batch', nc_input=1, nc_max=128, nc_l1=8, nc_step=1, nz_shape=20):
    ''' Simple 3D encoder with nlayers.
    
    Args:
        nlayers: number of encoder layers
        use_bn: whether to use batch_norm
        nc_input: number of input channels
        nc_max: number of max channels
        nc_l1: number of channels in layer 1
        nc_step: double number of channels every nc_step layers      
        nz_shape: size of bottleneck layer
    '''
    modules = []
    nc_output = nc_l1
    for nl in range(nlayers):
        if (nl>=1) and (nl%nc_step==0) and (nc_output <= nc_max*2):
            nc_output *= 2

        modules.append(conv3d(norm_type, nc_input, nc_output, stride=1))
        nc_input = nc_output
        modules.append(conv3d(norm_type, nc_input, nc_output, stride=1))
        modules.append(torch.nn.MaxPool3d(kernel_size=2, stride=2))

    modules.append(Flatten())
    modules.append(fc_stack(nc_output, nz_shape, 2, norm_type))
    encoder = nn.Sequential(*modules)
    net_init(encoder)
    return encoder, nc_output


def decoder3d(nlayers, nz_shape, nc_input, norm_type='batch', nc_final=1, nc_min=8, nc_step=1, init_fc=True):
    ''' Simple 3D encoder with nlayers.
    
    Args:
        nlayers: number of decoder layers
        nz_shape: number of bottleneck
        nc_input: number of channels to start upconvolution from
        use_bn: whether to use batch_norm
        nc_final: number of output channels
        nc_min: number of min channels
        nc_step: double number of channels every nc_step layers
        init_fc: initial features are not spatial, use an fc & unsqueezing to make them 3D
    '''
    modules = []
    if init_fc:
        modules.append(fc('batch', nz_shape, nc_input))
        for d in range(3):
            modules.append(Unsqueeze(2))
    nc_output = nc_input
    for nl in range(nlayers):
        if (nl%nc_step==0) and (nc_output//2 >= nc_min):
            nc_output = nc_output//2

        modules.append(deconv3d(norm_type, nc_input, nc_output))
        nc_input = nc_output
        modules.append(conv3d(norm_type, nc_input, nc_output))

    modules.append(nn.Conv3d(nc_output, nc_final, kernel_size=3, stride=1, padding=1, bias=True))
    decoder = nn.Sequential(*modules)
    net_init(decoder)
    return decoder


def net_init(net):
    for m in net.modules():
        if isinstance(m, nn.Linear):
            m.weight.data.normal_(0, 0.02)
            if m.bias is not None:
                m.bias.data.zero_()

        if isinstance(m, nn.Conv2d): #or isinstance(m, nn.ConvTranspose2d):
            m.weight.data.normal_(0, 0.02)
            if m.bias is not None:
                m.bias.data.zero_()

        if isinstance(m, nn.ConvTranspose2d):
            # Initialize Deconv with bilinear weights.
            base_weights = bilinear_init(m.weight.data.size(-1))
            base_weights = base_weights.unsqueeze(0).unsqueeze(0)
            m.weight.data = base_weights.repeat(m.weight.data.size(0), m.weight.data.size(1), 1, 1)
            if m.bias is not None:
                m.bias.data.zero_()

        if isinstance(m, nn.Conv3d) or isinstance(m, nn.ConvTranspose3d):
            m.weight.data.normal_(0, 0.02)
            if m.bias is not None:
                m.bias.data.zero_()

        elif isinstance(m, nn.BatchNorm2d) or isinstance(m, nn.BatchNorm3d):
            m.weight.data.fill_(1)
            m.bias.data.zero_()


def bilinear_init(kernel_size=4):
    # Following Caffe's BilinearUpsamplingFiller
    # https://github.com/BVLC/caffe/pull/2213/files
    import numpy as np
    width = kernel_size
    height = kernel_size
    f = int(np.ceil(width / 2.))
    cc = (2 * f - 1 - f % 2) / (2.*f)
    weights = torch.zeros((height, width))
    for y in range(height):
        for x in range(width):
            weights[y, x] = (1 - np.abs(x / f - cc)) * (1 - np.abs(y / f - cc))

    return weights


if __name__ == '__main__':
    decoder2d(5, None, 256, use_deconv=True, init_fc=False)
    bilinear_init()
