import datetime
import csv

import tensorflow as tf
from tensorflow.keras import layers

from level_parser import SokoLevel, SokoTile, logger


PAD_WIDTH = 50
PAD_HEIGHT = 50

def read_dataset(dataset: str, pad_width: int, pad_height: int):
    "Read the csv dataset of unpadded level strings and solvability labels, pad them and return"
    levels = []
    labels = []
    with open(dataset, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            level_desc = row['level_desc'] # level description
            is_solvable = bool(row['is_solvable'] == 'True')
            level = SokoLevel.from_str(level_desc)
            level._pad_level(pad_width, pad_height)
            levels.append(level)
            labels.append(is_solvable)
    return levels, labels

def create_model(pad_width: int, pad_height: int) -> tf.keras.Model:
    inputs = layers.Input(shape=(pad_width, pad_height, len(SokoTile)))
    
    x = inputs
    x = layers.Conv2D(1, 1, activation='relu')(x)
    x = layers.Conv2D(16, 10, activation='relu')(x)
    # x = layers.Conv2D(8, 15, activation='relu')(x)
    # x = layers.Conv2D(4, 20, activation='relu')(x)
    x = layers.Flatten()(x)
    x = layers.Dense(10, activation='tanh')(x)
    x = layers.Dense(10, activation='tanh')(x)
    outputs = layers.Dense(1, activation='sigmoid')(x)

    model = tf.keras.Model(inputs=inputs, outputs=outputs, name="sokoban_solvability_prediction_model")
    logger.info(model.summary())
    return model

def load_level_dataset(pad_width: int, pad_height: int, test_train_split: float=0.2):
    levels, labels = read_dataset('is_solvable.csv', pad_width, pad_height)
    levels = list(map(lambda sokolevel: sokolevel.as_numlist(), levels))
    print(levels[0])

    levels_tensor = tf.convert_to_tensor(levels, dtype=tf.int32)
    logger.debug(f'Levels tensor shape: {levels_tensor.shape}')
    levels_1he = tf.one_hot(levels_tensor, depth=len(SokoTile))

    labels_tensor = tf.reshape(tf.convert_to_tensor(labels, dtype=tf.int32), shape=(len(levels), 1))

    indices = tf.range(start=0, limit=tf.shape(levels_1he)[0], dtype=tf.int32)
    idx = tf.random.shuffle(indices)
    
    levels_1he_shuffled = tf.gather(levels_1he, idx)
    labels_shuffled = tf.gather(labels_tensor, idx)

    logger.info(f'Levels shape: {levels_1he_shuffled.shape}')
    logger.info(f'Labels shape: {labels_shuffled.shape}')

    # TODO: use tfds to do this (or tf.data)
    num_test = int(len(levels) * test_train_split)
    x_test = levels_1he_shuffled[-num_test:]
    y_test = labels_shuffled[-num_test:]
    x_train = levels_1he_shuffled[:-num_test]
    y_train = labels_shuffled[:-num_test]

    pos_train = int(tf.math.count_nonzero(y_train))
    size_train = int(tf.size(y_train))
    pos_test = int(tf.math.count_nonzero(y_test))
    size_test = int(tf.size(y_test))

    print(f'Class balance (train): {pos_train} / {size_train - pos_train} ({(pos_train / size_train) * 100}%)')
    print(f'Class balance (test): {pos_test} / {size_test - pos_test} ({(pos_test / size_test) * 100}%)')

    return (x_train, y_train), (x_test, y_test)

def train_model(model, x_train, y_train, validation_share: float=0.2):
    num_validation = int(len(x_train) * validation_share)
    x_val = x_train[-num_validation:]
    y_val = y_train[-num_validation:]
    x_train = x_train[:-num_validation]
    y_train = y_train[:-num_validation]

    model.compile(
        optimizer = tf.keras.optimizers.SGD(),
        loss = tf.keras.losses.BinaryCrossentropy(),
        metrics = [
            tf.keras.metrics.BinaryAccuracy(), 
            tf.keras.metrics.TruePositives(), 
            tf.keras.metrics.TrueNegatives(),
            tf.keras.metrics.FalsePositives(),
            tf.keras.metrics.FalseNegatives(),
        ]
    )

    log_dir = "logs/fit/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir, histogram_freq=1)

    history = model.fit(
        x_train,
        y_train,
        batch_size=8,
        epochs=10,
        validation_data=(x_val, y_val),
        # callbacks=[tensorboard_callback]
    )

    return history

def test_model(model, x_test, y_test):
    results = model.evaluate(x_test, y_test, batch_size=8, return_dict=True)
    return results

if __name__ == '__main__':
    (x_train, y_train), (x_test, y_test) = load_level_dataset(PAD_WIDTH, PAD_HEIGHT)
    model = create_model(PAD_WIDTH, PAD_HEIGHT)
    history = train_model(model, x_train, y_train)
    results = test_model(model, x_test, y_test)
    print(history)
    print(results)
