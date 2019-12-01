# !/usr/bin/env python

"""
Fully Connected network has been updated here
Last layer is splitted into user size and used softmax to classify signal
Second last layer also splitted into four equal parts
"""

import tensorflow as tf
import numpy as np
import time as tm
import matplotlib.pyplot as plt

# parameters
user = 20 # 8  # 20
antenna = 30 # 16  # 30

num_snr = 6
low_snr_db_train = 7.0
high_snr_db_train = 14.0
low_snr_db_test = 7.0  # 8.0
high_snr_db_test = 14.0  # 13.0

low_snr_train = 10.0 ** (low_snr_db_train/10.0)
high_snr_train = 10.0 ** (high_snr_db_train/10.0)
low_snr_test = 10.0 ** (low_snr_db_test/10.0)
high_snr_test = 10.0 ** (high_snr_db_test/10.0)

batch_size = 1000  # 1000
train_iter = 10000  # 1000000
test_iter = 1000
fc_size = 200  # user * user * user # 200
num_of_hidden_layers = 5  # user
startingLearningRate = .0003  # 0.0003
decay_factor = 0.97  # 0.97
decay_step_size = 1000

bers = np.zeros((1, num_snr))
bers_2 = np.zeros((1, num_snr))

H = np.genfromtxt('Top06_30_20.csv', dtype=None, delimiter=',')


def weight_variable(shape):
    initial = tf.truncated_normal(shape, stddev=0.05)
    return tf.Variable(initial)


def bias_variable(shape):
    initial = tf.constant(0.1, shape=shape)
    return tf.Variable(initial)


def constellation_alphabet(mod):
    if mod == 'BPSK':
        return np.array([[-1, 1]], np.float)
    elif mod == 'QPSK':
        return np.array([[-1, 1]], np.float)
    elif mod == '16QAM':
        return np.array([[-3, -1, 1, 3]], np.float)
    elif mod == '64QAM':
        return np.array([[-7, -5, -3, -1, 1, 3, 5, 7]], np.float)

def generate_data_train(B, K, N, snr_low, snr_high, H_org):
    # H_ = np.random.randn(B, N, K)
    # W_ = np.zeros([B, K, K])
    rand_symbol_ind = (np.random.randint(low = 0, high = CONS_ALPHABET.shape[1], size = (B*K, 1))).flatten()
    transmitted_symbol = (CONS_ALPHABET[:, rand_symbol_ind])

    x_ = transmitted_symbol.reshape(B, K)

    length_one_hot_vector = CONS_ALPHABET.shape[1]
    x_one_hot = generate_one_hot(x_, B, K, length_one_hot_vector)
    y_ = np.zeros([B, N])
    w = np.random.randn(B, N)
    H_ = np.zeros([B, N, K])
    Hy_ = x_ * 0
    HH_ = np.zeros([B, K, K])
    SNR_ = np.zeros([B])
    for i in range(B):
        SNR = np.random.uniform(low=snr_low, high=snr_high)
        H = H_org
        #H = H_[i, :, :]
        tmp_snr = (H.T.dot(H)).trace() / K
        H_[i, :, :] = H
        y_[i, :] = (H.dot(x_[i, :]) + w[i, :] * np.sqrt(tmp_snr) / np.sqrt(SNR))
        Hy_[i, :] = H.T.dot(y_[i, :])
        HH_[i, :, :] = H.T.dot(H_[i, :, :])
        SNR_[i] = SNR
    return y_, H_, Hy_, HH_, x_, SNR_, x_one_hot


def generate_data_iid_test(B, K, N, snr_low,snr_high):
    H_=np.random.randn(B, N, K)
    # W_=np.zeros([B,K,K])
    x_= np.sign(np.random.rand(B, K)-0.5)
    y_= np.zeros([B,N])
    w = np.random.randn(B,N)
    Hy_ = x_ * 0
    HH_ = np.zeros([B, K, K])
    SNR_ = np.zeros([B])

    for i in range(B):
        SNR = np.random.uniform(low=snr_low,high=snr_high)
        H = H_[i,:,:]
        tmp_snr =(H.T.dot(H)).trace()/K
        H_[i,:,:] = H
        y_[i,:] = (H.dot(x_[i,:])+w[i,:]*np.sqrt(tmp_snr)/np.sqrt(SNR))
        Hy_[i,:] = H.T.dot(y_[i,:])
        HH_[i,:,:] = H.T.dot( H_[i,:,:])
        SNR_[i] = SNR
        print(y_)
    return y_,H_,Hy_,HH_,x_,SNR_


def generate_one_hot(symbol, B, K, length_one_hot):
    depth_one_hot_vector = CONS_ALPHABET.shape[1]
    reset_symbol = symbol + np.multiply(np.ones([B, K]), (abs(np.amin(CONS_ALPHABET, 1)) + 1))
    one_hot_vector = tf.one_hot(reset_symbol, depth_one_hot_vector, on_value=1.0, off_value=0.0, axis=-1)
    one_hot_arr = sess.run(one_hot_vector)
    one_hot_vector_reshaped = one_hot_arr.reshape(B, K, length_one_hot)
    return one_hot_vector_reshaped


def hidden_layer(x,input_size,output_size,Layer_num):
    W = tf.Variable(tf.random_normal([input_size, output_size], stddev=0.01))
    w = tf.Variable(tf.random_normal([1, output_size], stddev=0.01))
    y = tf.matmul(x, W)+w
    return y


def activation_fn(x,input_size,output_size,Layer_num):
    y = tf.nn.relu(hidden_layer(x,input_size,output_size,Layer_num))
    return y


def error_rate(transmitted_symbol, estimated_symbol):
    trasmitted_symbol_stacked = transmitted_symbol
    estimated_symbol_stacked = estimated_symbol

    v1 = np.matmul(estimated_symbol_stacked, np.ones([1, CONS_ALPHABET.size]))
    v2 = np.matmul(np.ones([user * batch_size, 1]), CONS_ALPHABET)

    idxhat = np.argmin(np.square(np.abs(v1 - v2)), axis=1)

    idx = CONS_ALPHABET[:, idxhat]
    accuracy_zf = np.equal(idx.flatten(), np.transpose(trasmitted_symbol_stacked))

    error_zf = 1 - (np.sum(accuracy_zf) / (user * batch_size))

    return error_zf
'''..................................................................................................................'''
sess = tf.InteractiveSession()

CONS_ALPHABET = constellation_alphabet('QPSK')
length_one_hot_vector = CONS_ALPHABET.shape[1]


received_sig = tf.placeholder(tf.float32, shape=[None, user], name='input')
transmitted_sig = tf.placeholder(tf.float32, shape=[None, user], name='org_siganl')
batchSize = tf.placeholder(tf.int32)
batch_x_one_hot = tf.placeholder(tf.float32, shape=[None, user, length_one_hot_vector], name='one_hot_org_siganl')


# The network
h_fc = []
W_fc_input = weight_variable([user, fc_size])
b_fc_input = bias_variable([fc_size])
h_fc.append(tf.nn.relu(tf.matmul(received_sig, W_fc_input) + b_fc_input))

for i in range(num_of_hidden_layers):
    h_fc.append(activation_fn(h_fc[i - 1], fc_size, fc_size, 'relu' + str(i)))

W_fc_final = weight_variable([fc_size, user])
b_final = bias_variable([user])
h_final = tf.matmul(h_fc[i], W_fc_final) + b_final

ssd = tf.reduce_sum(tf.square(transmitted_sig - h_final))

global_step = tf.Variable(0, trainable=False)
learning_rate = tf.train.exponential_decay(startingLearningRate, global_step, decay_step_size, decay_factor,
                                           staircase=True)
train_step = tf.train.AdamOptimizer(learning_rate).minimize(ssd)


val = tf.reshape(transmitted_sig, tf.stack([user * batchSize]))
val_2 = tf.reshape(transmitted_sig, [user * batch_size, 1])
final_2 = tf.reshape(h_final, [user * batch_size, 1])
final = tf.reshape(h_final, tf.stack([user * batchSize]))
rounded = tf.sign(final)
eq = tf.equal(rounded, val)
eq2 = tf.reduce_sum(tf.cast(eq, tf.int32))

#eq3 = error_rate(val_2, final_2)

accuracy = ssd

sess.run(tf.global_variables_initializer())
"""
training phase og the network
"""
for i in range(train_iter):
    batch_Y, batch_H, batch_HY, batch_HH, batch_X, SNR1, one_hot = generate_data_train(batch_size, user, antenna, low_snr_train, high_snr_train, H)
    if i % 100 == 0:
        correct_bits = eq2.eval(feed_dict={received_sig: batch_HY, transmitted_sig: batch_X, batchSize: batch_size})
        train_accuracy = accuracy.eval(feed_dict={received_sig: batch_HY, transmitted_sig: batch_X, batchSize: batch_size})
        val_3, final_3 = sess.run([val_2, final_2], feed_dict={received_sig: batch_HY, transmitted_sig: batch_X, batchSize: batch_size})
        eq3 = error_rate(val_3, final_3)
        print("step %d, loss is %g, number of correct bits %d" % (i, train_accuracy, correct_bits))
        print('Error_', eq3)
    train_step.run(feed_dict={received_sig: batch_HY, transmitted_sig: batch_X, batchSize: batch_size})

"""
start testing our net
"""
tmp_bers = np.zeros((1, test_iter))
tmp_bers_2 = np.zeros((1, test_iter))
tmp_times = np.zeros((1, test_iter))
times = np.zeros((1, 1))
testHitCount = 0

snr_list_db = np.linspace(low_snr_db_test, high_snr_db_test, num_snr)
snr_list = 10.0 ** (snr_list_db / 10.0)

for i_snr in range(num_snr):
    Cur_SNR = snr_list[i_snr]
    print('cur snr')
    print(Cur_SNR)
    for i in range(test_iter):
        batch_Y, batch_H, batch_HY, batch_HH, batch_X, SNR1, one_hot = generate_data_train(batch_size, user, antenna, Cur_SNR, Cur_SNR)
        tic = tm.time()
        tmp_bers[0][i] = eq2.eval(feed_dict={received_sig: batch_HY, transmitted_sig: batch_X, batchSize: batch_size})
        val_3, final_3 = sess.run([val_2, final_2], feed_dict={received_sig: batch_HY, transmitted_sig: batch_X, batchSize: batch_size})
        tmp_bers_2[0][i] = error_rate(val_3, final_3)
        toc = tm.time()
        tmp_times[0][i] = toc - tic
        if i % 100 == 0:
            eq2.eval(feed_dict={received_sig: batch_HY, transmitted_sig: batch_X, batchSize: batch_size})
            train_accuracy = accuracy.eval(feed_dict={received_sig: batch_HY, transmitted_sig: batch_X, batchSize: batch_size})
            print("test accuracy %g" % eq2.eval(feed_dict={received_sig: batch_HY, transmitted_sig: batch_X, batchSize: batch_size}))

    bers[0][i_snr] = np.mean(tmp_bers[0])
    bers_2[0][i_snr] = np.mean(tmp_bers_2[0])

times[0][0] = np.mean(tmp_times[0]) / batch_size
print('Average time to detect a single K bit signal is:')
print(times)
bers = bers / (user * batch_size)
bers = 1 - bers
snrdb_list = np.linspace(low_snr_db_test, high_snr_db_test, num_snr)
print('snrdb_list')
print(snrdb_list)
print('Bit error rates are:')
print(bers)

fig2 = plt.figure('BPSK, TxR=20x30, Iteration=1000,SNR=7-14')
#fig2 = plt.figure('Python, 64QAM, TxR=16x32, Iteration=100000,SNR=10-3-38')
#fig2 = plt.figure('Python, 64QAM, TxR=16x32, Iteration=100000,SNR=-2-2-16, WRONG RESULT')
ax2 = fig2.add_subplot(111)
ax2.plot(snrdb_list.reshape(-1), bers.reshape(-1), color='black', marker='*', linestyle='-', linewidth=1, markersize=6, label='FC')
ax2.plot(snrdb_list.reshape(-1), bers_2.reshape(-1), color='blue', marker='d', linestyle='-', linewidth=1, markersize=6, label='FC_MMSE')
#ax2.plot(snr_db_list, bers_mmse, color='black', marker='*', linestyle='-', linewidth=1, markersize=6, label='MMSE')
#ax2.plot(snr_db_list, bers_zf, color='blue', marker='d', linestyle='-', linewidth=1, markersize=5, label='ZF')
#ax2.plot(snr_db_list, bers_mf, color='red', marker='x', linestyle='-', linewidth=1, markersize=6, label='MF')
#ax2.plot(snr_db_list, bers_sd, color='magenta', marker='s', linestyle='-', linewidth=1, markersize=6, label='SD')
ax2.set_title('BER vs SNR')
ax2.set_xlabel('SNR(dB)')
ax2.set_ylabel('BER')
ax2.set_yscale('log')
ax2.set_ylim(0.0001, 1)
ax2.set_xlim(8, 13)
plt.grid(b=True, which='major', color='#666666', linestyle='--')
plt.legend(title='Detectors:')
plt.show()