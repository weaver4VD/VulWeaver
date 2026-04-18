import { PerspectiveCard } from '../../../plugins/perspectiveimage.js';
import Clone from '../../../plugins/utils/object/Clone.js';

const GetValue = Phaser.Utils.Objects.GetValue;

var CreatePerspectiveCardMesh = function (config) {
    var scene = this.scene;

    this.setSnapshotPadding(GetValue(config, 'snapshotPadding', 0));

    config = Clone(config);
    delete config.width;
    delete config.height;
    config.front = { width: 1, height: 1 };
    config.back = { width: 1, height: 1 };
    var card = new PerspectiveCard(scene, config);
    scene.add.existing(card);

    var flip = card.flip;
    if (flip) {
        var parent = this;
        flip
            .on('start', function () {
                parent.enterPerspectiveMode();
            })
            .on('complete', function () {
                parent.exitPerspectiveMode();
            })
    }

    return card;
}

export default CreatePerspectiveCardMesh;