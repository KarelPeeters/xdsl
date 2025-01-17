from __future__ import annotations
from typing import Annotated, List, cast

from xdsl.dialects.builtin import IndexType, VectorType, i1
from xdsl.dialects.memref import MemRefType
from xdsl.ir import Attribute, Operation, SSAValue, Dialect, OpResult
from xdsl.irdl import AnyAttr, irdl_op_definition, Operand, VarOperand
from xdsl.utils.exceptions import VerifyException


@irdl_op_definition
class Load(Operation):
    name = "vector.load"
    memref: Annotated[Operand, MemRefType]
    indices: Annotated[VarOperand, IndexType]
    res: Annotated[OpResult, VectorType]

    def verify_(self):
        if not isinstance(self.memref.typ, MemRefType):
            raise VerifyException("expected a memref type")

        memref_typ = cast(MemRefType[Attribute], self.memref.typ)

        if not isinstance(self.res.typ, VectorType):
            raise VerifyException("expected a vector type")

        res_typ = cast(VectorType[Attribute], self.res.typ)

        if memref_typ.element_type != res_typ.element_type:
            raise VerifyException(
                "MemRef element type should match the Vector element type.")

        if self.memref.typ.get_num_dims() != len(self.indices):
            raise VerifyException("Expected an index for each dimension.")

    @staticmethod
    def get(ref: SSAValue | Operation,
            indices: List[SSAValue | Operation]) -> Load:
        return Load.build(operands=[ref, indices],
                          result_types=[
                              VectorType.from_element_type_and_shape(
                                  SSAValue.get(ref).typ.element_type, [1])
                          ])


@irdl_op_definition
class Store(Operation):
    name = "vector.store"
    vector: Annotated[Operand, VectorType]
    memref: Annotated[Operand, MemRefType]
    indices: Annotated[VarOperand, IndexType]

    def verify_(self):
        if not isinstance(self.memref.typ, MemRefType):
            raise VerifyException("expected a memref type")

        memref_typ = cast(MemRefType[Attribute], self.memref.typ)

        if not isinstance(self.vector.typ, VectorType):
            raise VerifyException("expected a vector type")

        vector_typ = cast(VectorType[Attribute], self.vector.typ)

        if memref_typ.element_type != vector_typ.element_type:
            raise VerifyException(
                "MemRef element type should match the Vector element type.")

        if self.memref.typ.get_num_dims() != len(self.indices):
            raise VerifyException("Expected an index for each dimension.")

    @staticmethod
    def get(vector: Operation | SSAValue, ref: Operation | SSAValue,
            indices: List[Operation | SSAValue]) -> Store:
        return Store.build(operands=[vector, ref, indices])


@irdl_op_definition
class Broadcast(Operation):
    name = "vector.broadcast"
    source: Annotated[Operand, AnyAttr()]
    vector: Annotated[OpResult, VectorType]

    def verify_(self):
        if not isinstance(self.vector.typ, VectorType):
            raise VerifyException("expected a vector type")

        vector_typ = cast(VectorType[Attribute], self.vector.typ)

        if self.source.typ != vector_typ.element_type:
            raise VerifyException(
                "Source operand and result vector must have the same element type."
            )

    @staticmethod
    def get(source: Operation | SSAValue) -> Broadcast:
        return Broadcast.build(operands=[source],
                               result_types=[
                                   VectorType.from_element_type_and_shape(
                                       SSAValue.get(source).typ, [1])
                               ])


@irdl_op_definition
class FMA(Operation):
    name = "vector.fma"
    lhs: Annotated[Operand, VectorType]
    rhs: Annotated[Operand, VectorType]
    acc: Annotated[Operand, VectorType]
    res: Annotated[OpResult, VectorType]

    def verify_(self):
        res_element_type = self.res.typ.element_type
        res_shape = self.res.typ.get_shape()

        if res_element_type != self.lhs.typ.element_type:
            raise VerifyException(
                "Result vector type must match with all source vectors. Found different types for result vector and lhs vector."
            )
        elif res_element_type != self.rhs.typ.element_type:
            raise VerifyException(
                "Result vector type must match with all source vectors. Found different types for result vector and rhs vector."
            )
        elif res_element_type != self.acc.typ.element_type:
            raise VerifyException(
                "Result vector type must match with all source vectors. Found different types for result vector and acc vector."
            )

        if res_shape != self.lhs.typ.get_shape():
            raise VerifyException(
                "Result vector shape must match with all source vector shapes. Found different shapes for result vector and lhs vector."
            )
        elif res_shape != self.rhs.typ.get_shape():
            raise VerifyException(
                "Result vector shape must match with all source vector shapes. Found different shapes for result vector and rhs vector."
            )
        elif res_shape != self.acc.typ.get_shape():
            raise VerifyException(
                "Result vector shape must match with all source vector shapes. Found different shapes for result vector and acc vector."
            )

    @staticmethod
    def get(lhs: Operation | SSAValue, rhs: Operation | SSAValue,
            acc: Operation | SSAValue) -> FMA:
        return FMA.build(operands=[lhs, rhs, acc],
                         result_types=[
                             VectorType.from_element_type_and_shape(
                                 SSAValue.get(lhs).typ.element_type, [1])
                         ])


@irdl_op_definition
class Maskedload(Operation):
    name = "vector.maskedload"
    memref: Annotated[Operand, MemRefType]
    indices: Annotated[VarOperand, IndexType]
    mask: Annotated[Operand, VectorType]
    passthrough: Annotated[Operand, VectorType]
    res: Annotated[OpResult, VectorType]

    def verify_(self):
        memref_element_type = self.memref.typ.element_type

        if memref_element_type != self.res.typ.element_type:
            raise VerifyException(
                "MemRef element type should match the result vector and passthrough vector element type. Found different element types for memref and result."
            )
        elif memref_element_type != self.passthrough.typ.element_type:
            raise VerifyException(
                "MemRef element type should match the result vector and passthrough vector element type. Found different element types for memref and passthrough."
            )

        if len(self.res.typ.get_shape()) != 1:
            raise VerifyException("Expected a rank 1 result vector.")

        if len(self.mask.typ.get_shape()) != 1:
            raise VerifyException("Expected a rank 1 mask vector.")

        if self.mask.typ.element_type != i1:
            raise VerifyException("Expected mask element type to be i1.")

        if self.memref.typ.get_num_dims() != len(self.indices):
            raise VerifyException(
                "Expected an index for each memref dimension.")

    @staticmethod
    def get(memref: SSAValue | Operation, indices: List[SSAValue | Operation],
            mask: SSAValue | Operation,
            passthrough: SSAValue | Operation) -> Maskedload:
        return Maskedload.build(operands=[memref, indices, mask, passthrough],
                                result_types=[
                                    VectorType.from_element_type_and_shape(
                                        SSAValue.get(memref).typ.element_type,
                                        [1])
                                ])


@irdl_op_definition
class Maskedstore(Operation):
    name = "vector.maskedstore"
    memref: Annotated[Operand, MemRefType]
    indices: Annotated[VarOperand, IndexType]
    mask: Annotated[Operand, VectorType]
    value_to_store: Annotated[Operand, VectorType]

    def verify_(self):
        memref_element_type = self.memref.typ.element_type

        if memref_element_type != self.value_to_store.typ.element_type:
            raise VerifyException(
                "MemRef element type should match the stored vector type. Obtained types were "
                + str(memref_element_type) + " and " +
                str(self.value_to_store.typ.element_type) + ".")

        if len(self.value_to_store.typ.get_shape()) != 1:
            raise VerifyException("Expected a rank 1 vector to be stored.")

        if len(self.mask.typ.get_shape()) != 1:
            raise VerifyException("Expected a rank 1 mask vector.")

        if self.mask.typ.element_type != i1:
            raise VerifyException("Expected mask element type to be i1.")

        if self.memref.typ.get_num_dims() != len(self.indices):
            raise VerifyException(
                "Expected an index for each memref dimension.")

    @staticmethod
    def get(memref: SSAValue | Operation, indices: List[SSAValue | Operation],
            mask: SSAValue | Operation,
            value_to_store: SSAValue | Operation) -> Maskedstore:
        return Maskedstore.build(
            operands=[memref, indices, mask, value_to_store])


@irdl_op_definition
class Print(Operation):
    name = "vector.print"
    source: Annotated[Operand, AnyAttr()]

    @staticmethod
    def get(source: Operation | SSAValue) -> Print:
        return Print.build(operands=[source])


@irdl_op_definition
class Createmask(Operation):
    name = "vector.create_mask"
    mask_operands: Annotated[VarOperand, IndexType]
    mask_vector: Annotated[OpResult, VectorType]

    def verify_(self):
        if self.mask_vector.typ.element_type != i1:
            raise VerifyException("Expected mask element type to be i1.")

        if self.mask_vector.typ.get_num_dims() != len(self.mask_operands):
            raise VerifyException(
                "Expected an operand value for each dimension of resultant mask."
            )

    @staticmethod
    def get(mask_operands: Operation | SSAValue) -> Createmask:
        return Createmask.build(
            operands=[mask_operands],
            result_types=[VectorType.from_element_type_and_shape(i1, [1])])


Vector = Dialect(
    [Load, Store, Broadcast, FMA, Maskedload, Maskedstore, Print, Createmask],
    [])
