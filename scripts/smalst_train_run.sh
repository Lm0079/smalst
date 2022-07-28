 
#python -m smalst.experiments.smal_shape --zebra_dir='smalst/zebra_training_set' --num_epochs=40 --save_epoch_freq=20 --name=smal_net_0 --save_training_imgs=False --num_images=20000 --do_validation=False --texture=False --texture_map=False --uv_flow=False --batch_size=2 --nz_feat=16 --bottleneck_size=16

python -m smalst.experiments.smal_shape --zebra_dir='/user/work/gh18931/diss/datasets/zebra_training_set'  --num_epochs=210 --num_images=15000  --save_training_imgs=False --save_epoch_freq=5  --name=smal_net_test

