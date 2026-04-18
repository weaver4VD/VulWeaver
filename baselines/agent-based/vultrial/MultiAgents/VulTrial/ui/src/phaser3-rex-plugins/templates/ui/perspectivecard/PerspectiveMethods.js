const FaceIndexMap = ['front', 'back'];

export default {
    enterPerspectiveMode() {
        if (this.isInPerspectiveMode) {
            return this;
        }
        this.setChildVisible(this.perspectiveCard, true);
        this.snapshotFace(0);
        this.snapshotFace(1);
        this.setChildVisible(this.childrenMap.front, false);
        this.setChildVisible(this.childrenMap.back, false);
        this.perspectiveCard.setSize(this.width, this.height);

        return this;
    },

    exitPerspectiveMode() {
        if (!this.isInPerspectiveMode) {
            return this;
        }
        this.setChildVisible(this.perspectiveCard, false);
        var isFrontFace = (this.perspectiveCard.face === 0);
        this.setChildVisible(this.childrenMap.front, isFrontFace);
        this.setChildVisible(this.childrenMap.back, !isFrontFace);

        return this;
    },

    setSnapshotPadding(padding) {
        this.snapshotPadding = padding;
        return this;
    },

    snapshotFace(face) {
        if (typeof (face) === 'number') {
            face = FaceIndexMap[face];
        }

        var cardFace = this.perspectiveCard.faces[face];
        var faceChild = this.childrenMap[face];

        cardFace.rt.clear();

        var faceChildVisibleSave = faceChild.visible;
        faceChild.visible = true;

        var gameObjects = (faceChild.isRexContainerLite) ? faceChild.getAllVisibleChildren() : faceChild;
        cardFace.snapshot(
            gameObjects,
            { padding: this.snapshotPadding }
        );

        faceChild.visible = faceChildVisibleSave;

        return this;
    }

}