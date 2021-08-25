import logging

import tensorflow as tf
from tensorflow.keras import layers

from level_parser import SokoTile, process_data, logger

def encode_level(level):
    "Convert level into representation used for input to NN"
    return tf.one_hot(level, depth=len(SokoTile))

def create_model():
    inputs = layers.Input(shape=(50, 50, 7))

    x = layers.Flatten()(inputs)
    x = layers.Dense(10, activation='tanh')(x)
    x = layers.Dense(10, activation='tanh')(x)
    outputs = layers.Dense(1, activation='sigmoid')(x)

    model = tf.keras.Model(inputs=inputs, outputs=outputs, name="sokoban_solvability_prediction_model")
    logger.info(model.summary())
    return model
    
def get_labels(levels):
    # TODO: call a planner function to solve the level to determine the y-label
    labels = [1] * len(levels)
    return labels

def load_level_dataset(test_train_split=0.2):
    # TODO: write this
    # 1. obtain all level files in data/ via process_data
    # 2. convert every level file into tensor (probably first merge them all together into a giant
    #   tensor, then 1HE them in one go)
    # 3. pad the data to 50x50
    # 4. call a planner function to solve the level to determine the y-label
    # 5. use some split for test-train
    #    Any way to augment the level for non-solvability? Could iteratively remove one box and add
    #    the newly unsolvable level to the dataset
    # Potential level generators to try -
    # - http://ianparberry.com/techreports/LARC-2011-01.pdf
    # - https://github.com/AlliBalliBaba/Sokoban-Level-Generator
    # - https://digital.library.unt.edu/ark:/67531/metadc801887/m2/1/high_res_d/dissertation.pdf
    # - https://arxiv.org/pdf/2005.08368.pdf
    # - https://hosei.repo.nii.ac.jp/?action=repository_action_common_download&item_id=22740&item_no=1&attribute_id=22&file_no=1
    # - https://www.aaai.org/ocs/index.php/AIIDE/AIIDE16/paper/viewFile/14006/13595
    levels = process_data(max_width=50, max_height=50)
    levels_tensor = tf.convert_to_tensor(levels, dtype=tf.int32)
    levels_1he = tf.one_hot(levels_tensor, depth=len(SokoTile))

    labels = get_labels(levels)
    labels_tensor = tf.reshape(tf.convert_to_tensor(labels, dtype=tf.int32), shape=(len(levels), 1))

    indices = tf.range(start=0, limit=tf.shape(levels_1he)[0], dtype=tf.int32)
    idx = tf.random.shuffle(indices)
    
    levels_1he_shuffled = tf.gather(levels_1he, idx)
    labels_shuffled = tf.gather(labels_tensor, idx)

    logger.info(f'Levels shape: {levels_1he_shuffled.shape}')
    logger.info(f'Labels shape: {labels_shuffled.shape}')

    # TODO: use tfds to do this
    num_test = int(len(levels) * test_train_split)
    x_test = levels_1he_shuffled[-num_test:]
    y_test = labels_shuffled[-num_test:]
    x_train = levels_1he_shuffled[:-num_test]
    y_train = labels_shuffled[:-num_test]

    return (x_train, y_train), (x_test, y_test)

def train_model():
    (x_train, y_train), (x_test, y_test) = load_level_dataset()

    VALIDATION_SHARE = 0.2
    num_validation = int(len(x_train) * VALIDATION_SHARE)
    x_val = x_train[-num_validation:]
    y_val = y_train[-num_validation:]
    x_train = x_train[:-num_validation]
    y_train = y_train[:-num_validation]

    model = create_model()
    model.compile(
        optimizer = tf.keras.optimizers.SGD(),
        loss = tf.keras.losses.BinaryCrossentropy(),
        metrics = [tf.keras.metrics.BinaryAccuracy()]
    )

    history = model.fit(
        x_train,
        y_train,
        batch_size=64,
        epochs=2,
        validation_data=(x_val, y_val)
    )

    results = model.evaluate(x_test, y_test, batch_size=128)
    return history, results

if __name__ == '__main__':
    history, results = train_model()
    print(history)
    print(results)