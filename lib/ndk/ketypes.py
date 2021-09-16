import ptypes
from ptypes import *

from . import rtltypes, Ntddk
from .datatypes import *

class DISPATCHER_HEADER(pstruct.type):
    _fields_ = [
        (LONG, 'Lock'),
        (LONG, 'SignalState'),
        (LIST_ENTRY, 'WaitListHead'),
    ]

class KEVENT(pstruct.type):
    _fields_ = [
        (DISPATCHER_HEADER, 'Header'),
    ]

class KSEMAPHORE(pstruct.type):
    _fields_ = [
        (DISPATCHER_HEADER, 'Header'),
        (LONG, 'Limit'),
    ]

class KGATE(KEVENT): pass

class KSPIN_LOCK(ULONG_PTR): pass

class KDPC(pstruct.type):
    _fields_ = [
        (UCHAR, 'Type'),
        (UCHAR, 'Importance'),
        (USHORT, 'Number'),
        (lambda self: dyn.clone(LIST_ENTRY, _path_=('DpcListEntry',), _object_=P(KDPC)), 'DpcListEntry'),
        (PVOID, 'DeferredRoutine'),
        (PVOID, 'DeferredContext'),
        (PVOID, 'SystemArgument1'),
        (PVOID, 'SystemArgument2'),
        (PVOID, 'DpcData'),
    ]

class KSCB(pstruct.type):
    class _Spare1(pbinary.flags):
        _fields_ = [
            (4, 'Spare1'),
            (1, 'RankBias'),
            (1, 'HardCap'),
            (1, 'OverQuota'),
            (1, 'Inserted'),
        ]
    _fields_ = [
        (ULONGLONG, 'GenerationCycles'),
        (ULONGLONG, 'UnderQuotaCycleTarget'),
        (ULONGLONG, 'RankCycleTarget'),
        (ULONGLONG, 'LongTermCycles'),
        (ULONGLONG, 'LastReportedCycles'),
        (ULONGLONG, 'OverQuotaHistory'),
        (LIST_ENTRY, 'PerProcessorList'),
        (rtltypes.RTL_BALANCED_NODE, 'QueueNode'),
        (_Spare1, 'Spare1'),
        (UCHAR, 'Spare2'),
        (USHORT, 'ReadySummary'),
        (ULONG, 'Rank'),
        (dyn.array(LIST_ENTRY, 16), 'ReadyListHead'),
    ]

class KSCHEDULING_GROUP(pstruct.type):
    _fields_ = [
        (USHORT, 'Value'),
        (UCHAR, 'Type'),
        (UCHAR, 'HardCap'),
        (ULONG, 'RelativeWeight'),
        (ULONGLONG, 'QueryHistoryTimeStamp'),
        (LONGLONG, 'NotificationCycles'),
        (lambda self: dyn.clone(LIST_ENTRY, _path_=('SchedulingGroupList',), _object_=P(KSCHEDULING_GROUP)), 'SchedulingGroupList'),
        (P(KDPC), 'NotificationDpc'),
        (P(KSCB), 'PerProcessor'),
    ]

class KWAIT_STATUS_REGISTER(UCHAR):
    pass

class KAPC_STATE(pstruct.type):
    def __init__(self, **attrs):
        super(KAPC_STATE, self).__init__(**attrs)
        self._fields_ = F = []
        F.extend([
            (dyn.array(LIST_ENTRY, 2), 'ApcListHead'),
            (P(KPROCESS), 'Process'),
            (UCHAR, 'KernelApcInProgress'),
            (UCHAR, 'KernelApcPending'),
            (UCHAR, 'UserApcPending'),
        ])

class KAPC(pstruct.type):
    def __init__(self, **attrs):
        super(KAPC, self).__init__(**attrs)
        self._fields_ = F = []
        F.extend([
            (UCHAR, 'Type'),
            (UCHAR, 'SpareByte0'),
            (UCHAR, 'Size'),
            (UCHAR, 'SpareByte1'),
            (ULONG, 'SpareLong0'),
            (P(KTHREAD), 'Thread'),
            (LIST_ENTRY, 'ApcListEntry'),
            (PVOID, 'KernelRoutine'),
            (PVOID, 'RundownRoutine'),
            (PVOID, 'NormalRoutine'),
            (PVOID, 'NormalContext'),
            (PVOID, 'SystemArgument1'),
            (PVOID, 'SystemArgument2'),
            (CHAR, 'ApcStateIndex'),
            (CHAR, 'ApcMode'),
            (UCHAR, 'Inserted'),
        ])

class KWAIT_BLOCK(pstruct.type):
    def __init__(self, **attrs):
        super(KWAIT_BLOCK, self).__init__(**attrs)
        self._fields_ = F = []
        F.extend([
            (LIST_ENTRY, 'WaitListEntry'),
            (P(KTHREAD), 'Thread'),
            (PVOID, 'Object'),
            (P(KWAIT_BLOCK), 'NextWaitBlock'),
            (WORD, 'WaitKey'),
            (UCHAR, 'WaitType'),
            (UCHAR, 'SpareByte'),
        ])

class KQUEUE(pstruct.type):
    _fields_ = [
        (DISPATCHER_HEADER, 'Header'),
        (LIST_ENTRY, 'EntryListHead'),
        (ULONG, 'CurrentCount'),
        (ULONG, 'MaximumCount'),
        (LIST_ENTRY, 'ThreadListHead'),
    ]

class KTIMER(pstruct.type):
    _fields_ = [
        (DISPATCHER_HEADER, 'Header'),
        (ULARGE_INTEGER, 'DueTime'),
        (LIST_ENTRY, 'TimerListEntry'),
        (P(KDPC), 'Dpc'),
        (ULONG, 'Period'),
    ]

class GROUP_AFFINITY(pstruct.type):
    _fields_ = [
        (lambda self: ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'Mask'),
        (USHORT, 'Group'),
        #(dyn.array(USHORT, 3), 'Reserved'),
    ]

class KLOCK_ENTRY_LOCK_STATE(pstruct.type):
    _fields_ = [
        (PVOID, 'LockState'),
        (PVOID, 'SessionState'),
    ]

class KLOCK_ENTRY(pstruct.type, versioned):
    def __init__(self, **attrs):
        super(KLOCK_ENTRY, self).__init__(**attrs)
        self._fields_ = f = [
            (rtltypes.RTL_BALANCED_NODE, 'TreeNode'),
        ]

        if getattr(self, 'WIN64', False):
            f.extend([
                (ULONG, 'EntryFlags'),
                (ULONG, 'SpareFlags'),
                (KLOCK_ENTRY_LOCK_STATE, 'LockState'),
                (rtltypes.RTL_RB_TREE, 'OwnerTree'),
                (rtltypes.RTL_RB_TREE, 'WaiterTree'),
                (ULONGLONG, 'EntryLock'),
                (USHORT, 'AllBoosts'),
                (USHORT, 'IoNormalPriorityWaiterCount'),
                (USHORT, 'SparePad'),
                (dyn.block(2 if getattr(self, 'WIN64', False) else 0), 'padding(ParentValue)'),
            ])
        else:
            f.extend([
                (PVOID, 'ThreadUnsafe'),
                (KLOCK_ENTRY_LOCK_STATE, 'LockState'),
                (rtltypes.RTL_RB_TREE, 'OwnerTree'),
                (rtltypes.RTL_RB_TREE, 'WaiterTree'),
                (ULONG, 'EntryCount'),
                (USHORT, 'AllBoosts'),
                (USHORT, 'IoNormalPriorityWaiterCount'),
            ])
        return

class KTHREAD(pstruct.type, versioned):
    def __init__(self, **attrs):
        super(KTHREAD, self).__init__(**attrs)
        self._fields_ = f = []

        f.extend([
            (DISPATCHER_HEADER, 'Header'),
            (PVOID, 'SListFaultAddress'),
            (ULONGLONG, 'QuantumTarget'),
            (PVOID, 'InitialStack'),
            (PVOID, 'StackLimit'),
            (PVOID, 'StackBase'),
            (KSPIN_LOCK, 'ThreadLock'),
            (ULONGLONG, 'CycleTime'),
        ])

        if not getattr(self, 'WIN64', False):
            f.extend([
                (ULONG, 'HighCycleTime'),
                (PVOID, 'ServiceTable'),
            ])

        f.extend([
            (ULONG, 'CurrentRunTime'),
            (ULONG, 'ExpectedRunTime'),
            (PVOID, 'KernelStack'),
            (P(XSAVE_FORMAT), 'StateSaveArea'),
            #(P(KSCHEDULING_GROUP), 'SchedulingGroup'),
            (PVOID, 'SchedulingGroup'),
            (KWAIT_STATUS_REGISTER, 'WaitRegister'),
            (BOOLEAN, 'Running'),
            (dyn.array(BOOLEAN, 2), 'Alerted'),
            (ULONG, 'MiscFlags'),
            (ULONG, 'ThreadFlags'),
            (UCHAR, 'Tag'),
            (UCHAR, 'SystemHeteroCpuPolicy'),
            (UCHAR, 'UserHeteroCpuPolicy'),
            (UCHAR, 'SpecCtrl'),
            (ULONG, 'SystemCallNumber'),
            (ULONG, 'ReadyTime'),
            (PVOID, 'FirstArgument'),
            (P(Ntddk.KTRAP_FRAME), 'TrapFrame'),

            (KAPC_STATE, 'ApcState'),       # (unaligned)
            (CHAR, 'Priority'),
            (ULONG, 'UserIdealProcessor'),
        ])

        if not getattr(self, 'WIN64', False):
            f.extend([
                (ULONG, 'ContextSwitches'),
                (UCHAR, 'State'),
                (CHAR, 'Spare12'),
                (KIRQL, 'WaitIrql'),
                (KPROCESSOR_MODE, 'WaitMode'),
            ])

        f.extend([
            (LONG_PTR, 'WaitStatus'),
            (P(KWAIT_BLOCK), 'WaitBlockList'),
            (LIST_ENTRY, 'WaitListEntry'),
            (P(KQUEUE), 'Queue'),
            (PVOID, 'Teb'),
            (dyn.align(8), 'align(RelativeTimerBias)'),
            (ULONGLONG, 'RelativeTimerBias'),
            (KTIMER, 'Timer'),
        ])

        if getattr(self, 'WIN64', False):
            f.extend([
                (dyn.array(KWAIT_BLOCK, 4), 'WaitBlock'),     # (unaligned)
                (dyn.block(4), 'padding(WaitBlock)'),
                #(P(UMS_CONTROL_BLOCK), 'Ucb'),
                (PVOID, 'Ucb'),
                #(P(KUMS_CONTEXT_HEADER), 'Uch'),
                (PVOID, 'Uch'),
                (PVOID, 'TebMappedLowVa'),
                (LIST_ENTRY, 'QueueListEntry'),
                (ULONG, 'NextProcessor'),
                (LONG, 'QueuePriority'),
                (P(KPROCESS), 'Process'),
            ])
        else:
            f.extend([
                (dyn.array(KWAIT_BLOCK, 4), 'WaitBlock'),     # (unaligned)
                (LIST_ENTRY, 'QueueListEntry'),
                (ULONG, 'NextProcessor'),
                (LONG, 'QueuePriority'),
                (P(KPROCESS), 'Process'),
            ])

        f.extend([
            (GROUP_AFFINITY, 'UserAffinity'),   # (unaligned)
            (CHAR, 'PreviousMode'),
            (CHAR, 'BasePriority'),
            (CHAR, 'PriorityDecrement'),
            (UCHAR, 'Preempted'),
            (UCHAR, 'AdjustReason'),
            (CHAR, 'AdjustIncrement'),
        ])

        f.extend([
            (GROUP_AFFINITY, 'Affinity'),   # (unaligned)
            (UCHAR, 'ApcStateIndex'),
            (UCHAR, 'WaitBlockCount'),
            (ULONG, 'IdealProcessor'),

            (dyn.array(P(KAPC_STATE), 2), 'ApcStatePointer'),

            (KAPC_STATE, 'SavedApcState'),  # (unaligned)
            (UCHAR, 'WaitReason'),

            (CHAR, 'SuspendCount'),
            (CHAR, 'Saturation'),
            (USHORT, 'SListFaultCount'),

            (KAPC, 'SchedulerApc'),         # (unaligned)
            (UCHAR, 'CallbackNestingLevel'),

            (ULONG, 'UserTime'),
            (KEVENT, 'SuspendEvent'),
            (LIST_ENTRY, 'ThreadListEntry'),
            (LIST_ENTRY, 'MutantListHead'),
            (SINGLE_LIST_ENTRY, 'LockEntriesFreeList'),
            (dyn.array(KLOCK_ENTRY, 6), 'LockEntries'),
            (SINGLE_LIST_ENTRY, 'PropagateBoostsEntry'),
            (SINGLE_LIST_ENTRY, 'IoSelfBoostsEntry'),
            (dyn.array(UCHAR, 16), 'PriorityFloorsCount'),
            (ULONG, 'PriorityFloorSummary'),
            (LONG, 'AbCompletedIoBoostCount'),
            (SHORT, 'AbReferenceCount'),
            (UCHAR, 'AbFreeEntryCount'),
            (UCHAR, 'AbWaitEntryCount'),
            (ULONG, 'ForegroundLossTime'),
            (LIST_ENTRY, 'GlobalForegroundListEntry'),
        ])

        if getattr(self, 'WIN64', False):
            f.extend([
                (LONGLONG, 'ReadOperationCount'),
                (LONGLONG, 'WriteOperationCount'),
                (LONGLONG, 'OtherOperationCount'),
                (LONGLONG, 'ReadTransferCount'),
                (LONGLONG, 'WriteTransferCount'),
                (LONGLONG, 'OtherTransferCount'),
            ])
        return

class KPROCESS(pstruct.type, versioned):
    def __init__(self, **attrs):
        super(KPROCESS, self).__init__(**attrs)
        self._fields_ = f = []
