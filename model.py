import tensorflow as tf

from level_parser import SokoTile

def encode_level(level):
    "Convert level into representation used for input to NN"
    return tf.one_hot(level, depth=len(SokoTile))

def create_model():
    inputs = tf.keras.Input(shape=(50, 50, 7))

    x = tf.keras.Dense(10, activation='tanh')(inputs)
    x = tf.keras.Dense(10, activation='tanh')(x)
    outputs = tf.keras.Dense(1, activation='sigmoid')(x)

    return tf.keras.Model(inputs=inputs, outputs=outputs, name="sokoban_solvability_prediction_model")

def load_level_dataset():
    # TODO: write this
    # 1. obtain all level files in data/ via process_data
    # 2. convert every level file into tensor (probably first merge them all together into a giant
    #   tensor, then 1HE them in one go)
    # 3. pad the data to 50x50
    # 4. call a planner function to solve the level to determine the y-label
    # 5. use some split for test-train
    #    Any way to augment the level for non-solvability? Could iteratively remove one box and add
    #    the newly unsolvable level to the dataset
    pass

if __name__ == '__main__':
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
