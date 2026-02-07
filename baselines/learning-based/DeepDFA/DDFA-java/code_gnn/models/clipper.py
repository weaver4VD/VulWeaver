import torch
import torch.nn.functional as F
import tqdm


def simple_union(a, b):
    """
    Return bitwise union of a and b.
    Source: https://discuss.pytorch.org/t/compute-gradient-of-bitwise-or/63189/4
    """
    y = (a + b) - (a * b)
    if torch.any(torch.isnan(y)):
        print("isnan", y)
    return y


def relu_union(a, b):
    """
    Return bitwise union of a and b.
    """
    shape = a.shape
    y = torch.ones(shape, device=a.device) - F.relu(torch.ones(shape, device=a.device) - (a + b))
    if torch.any(torch.isnan(y)):
        print("isnan", a, b, y)
    return y


def test_smoothness():
    def getitem(t, i):
        return round(t[i].item(), 2)

    for ai in tqdm.tqdm(
        torch.arange(-10, 10, step=0.01), "check result of ReLU bitwise union"
    ):
        b = torch.arange(-10, 10, step=0.01)
        a = torch.tensor([ai] * len(b))
        y = relu_union(a, b)
        for i in range(len(a)):
            if a[i] + b[i] < 1:
                expected = a[i] + b[i]
            else:
                expected = 1
            assert torch.abs(y[i] - expected) < 0.000001, (y[i], expected)


def dgl_union_factory(union_type):
    """
    Woah, nested factory
    """

    if union_type == "simple":
        union_fn = simple_union
    if union_type == "relu":
        union_fn = relu_union

    def dgl_union(msg, out):
        """
        Factory for dgl bitwise union function.
        """

        def _dgl_union(nodes):
            """
            UDF example from dgl.function.sum: https://docs.dgl.ai/en/0.6.x/generated/dgl.function.sum.html#dgl.function.sum
            Node-wise UDF: https://docs.dgl.ai/en/0.6.x/api/python/udf.html#node-wise-user-defined-function
            """
            union_result = nodes.data["h"]
            for i in range(nodes.mailbox[msg].shape[1]):
                union_result = union_fn(union_result, nodes.mailbox[msg][:, i, :])
            return {out: union_result}

        return _dgl_union

    return dgl_union


def test_union():
    """
    Simple graph:
    n1   n2
     |   |
     \  /
     v v
     n3
    """
    for mo in (simple_union, relu_union):
        n1 = torch.tensor([1, 0, 1, 0])
        n2 = torch.tensor([0, 0, 1, 1])
        union_result = mo(n1, n2)
        expected = torch.tensor([1, 0, 1, 1])
        assert torch.all(union_result.eq(expected)), (union_result, expected)
