"""
FoodSave AI — CNN Food Freshness Training Script
Run: python ai/train_model.py
Requires: pip install tensorflow pillow numpy
Dataset structure:
  ai/dataset/
    fresh/      ← images of fresh food
    stale/      ← images of stale/old food
    rotten/     ← images of rotten food
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# ── Config ──
IMG_SIZE    = (224, 224)
BATCH_SIZE  = 32
EPOCHS      = 20
DATASET_DIR = "ai/dataset"
MODEL_PATH  = "ai/freshness_model.h5"

# ── Data Augmentation ──
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    validation_split=0.2
)

train_gen = train_datagen.flow_from_directory(
    DATASET_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='training'
)

val_gen = train_datagen.flow_from_directory(
    DATASET_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation'
)

# ── Model (MobileNetV2 Transfer Learning) ──
base_model = tf.keras.applications.MobileNetV2(
    input_shape=(*IMG_SIZE, 3),
    include_top=False,
    weights='imagenet'
)
base_model.trainable = False  # Freeze base layers

model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.3),
    layers.Dense(train_gen.num_classes, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

print(f"\n✅ Classes: {train_gen.class_indices}")
print(f"✅ Training samples: {train_gen.samples}")

# ── Train ──
history = model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=EPOCHS,
    callbacks=[
        tf.keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True),
        tf.keras.callbacks.ModelCheckpoint(MODEL_PATH, save_best_only=True)
    ]
)

model.save(MODEL_PATH)
print(f"\n✅ Model saved to {MODEL_PATH}")
print(f"✅ Final accuracy: {max(history.history['val_accuracy']):.2%}")