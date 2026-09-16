# -*- coding: utf-8 -*-
"""
演示场景构建器
受 GPL v3.0 保护

创建89+个实体。
含受力点/接触面/组织/人员/设备。
"""

from typing import Dict, Any, List, Optional


class SceneBuilder:
    """演示场景构建器"""

    def __init__(self):
        self.entities: List[Any] = []
        self.entity_map: Dict[str, Any] = {}

    # ==================== 主入口 ====================

    def build_full_scene(self) -> Dict[str, Any]:
        """构建完整场景"""
        # 1. 组织
        orgs = self._build_organizations()
        # 2. 人员
        workers = self._build_workers()
        # 3. 车辆
        vehicles = self._build_vehicles()
        # 4. 结构
        structure = self._build_structure()
        # 5. 管道系统
        pipes = self._build_pipe_system()
        # 6. 其他专业
        others = self._build_other_disciplines()
        # 7. 图纸
        drawings = self._build_drawings()
        # 8. 合同
        contract = self._build_contract()
        # 9. 装配测试区
        test_area = self._build_assembly_test_area()

        # ★ A-2 新增：收集所有支架的锚点
        anchors = []
        for e in pipes:
            if hasattr(e, 'anchors'):
                anchors.extend(e.anchors)

        # ★ A-4 新增：从标准库生成 3 个任务
        from models.task_from_std import TaskFromStd
        demo_tasks = []
        task_types = ['安装支架', '安装管道', '系统试压']
        for ttype in task_types:
            try:
                task = TaskFromStd(task_type=ttype)
                demo_tasks.append(task)
            except ValueError as e:
                print(f"⚠️ 任务生成失败：{e}")

        # ★ A-5 新增：从标准库生成 1 个流程
        from models.process_from_std import ProcessFromStd
        demo_processes = []
        try:
            proc = ProcessFromStd(process_type='管道安装流程')
            # 关联实际的任务ID
            task_ids = [t.id for t in demo_tasks if t.task_type in ['安装支架', '安装管道', '系统试压']]
            proc.link_tasks(task_ids)
            demo_processes.append(proc)
        except ValueError as e:
            print(f"⚠️ 流程生成失败：{e}")

        # 建立任务之间的前后关系
        if len(demo_tasks) >= 2:
            demo_tasks[0].successor = [demo_tasks[1].id]
            demo_tasks[0].layer['l2_static_attributes']['后续任务'] = [demo_tasks[1].id]
        if len(demo_tasks) >= 3:
            demo_tasks[1].predecessor = demo_tasks[0].id
            demo_tasks[1].successor = [demo_tasks[2].id]
            demo_tasks[1].layer['l2_static_attributes']['前置任务'] = demo_tasks[0].id
            demo_tasks[1].layer['l2_static_attributes']['后续任务'] = [demo_tasks[2].id]
            demo_tasks[2].predecessor = demo_tasks[1].id
            demo_tasks[2].layer['l2_static_attributes']['前置任务'] = demo_tasks[1].id

        # ★ A-3 保留：为"安装支架"演示创建 4 个动作
        from models.action import ActionEntity
        demo_actions = []
        action_types = ['打孔', '装膨胀螺栓', '上支架', '锁紧支架']
        # 找出"安装支架"任务的ID
        install_support_task_id = 'TASK-DEMO-001'
        for t in demo_tasks:
            if t.task_type == '安装支架':
                install_support_task_id = t.id
                break
        for i, atype in enumerate(action_types):
            action = ActionEntity(
                action_type=atype,
                task_id=install_support_task_id,
                target_id='SUP-001',
                sequence=i + 1,
            )
            demo_actions.append(action)

        # 聚合
        self.entities = (orgs + workers + vehicles + structure + pipes + others +
                         drawings + [contract] + test_area + anchors + demo_actions +
                         demo_tasks + demo_processes)
        self.entity_map = {getattr(e, 'id', ''): e for e in self.entities if hasattr(e, 'id')}

        return {
            'entities': self.entities,
            'entity_map': self.entity_map,
            'summary': self.get_summary(),
        }

    # ==================== 构建方法 ====================

    def _build_organizations(self) -> List:
        """构建8个单位"""
        from models import OrganizationEntity
        orgs = []
        for code in ['owner', 'design', 'supervision', 'contractor',
                     'subcontractor', 'supplier', 'logistics', 'regulator']:
            orgs.append(OrganizationEntity(org_code=code))
        return orgs

    def _build_workers(self) -> List:
        """构建工人"""
        from models import WorkerEntity
        workers = []
        worker_data = [
            ('张三', 'con_foreman', 'contractor'),
            ('王五', 'pipefitter', 'contractor'),
            ('李四', 'deliverer', 'logistics'),
            ('赵六', 'welder', 'subcontractor'),
        ]
        for name, pos, org in worker_data:
            workers.append(WorkerEntity(name=name, position=pos, organization=org))
        return workers

    def _build_vehicles(self) -> List:
        """构建车辆"""
        from models import VehicleEntity
        return [
            VehicleEntity(plate_number='粤C·12345', vehicle_type='货车', capacity='3吨'),
            VehicleEntity(plate_number='粤C·67890', vehicle_type='叉车', capacity='1吨'),
        ]

    def _build_structure(self) -> List:
        """构建结构"""
        from models import WallEntity, SlabEntity, FloorEntity, ColumnEntity, CeilingEntity
        structure = []
        structure.append(WallEntity(length=10000, height=3000, thickness=240))
        structure.append(SlabEntity(length=10000, width=3000, thickness=120))
        structure.append(FloorEntity(length=10000, width=3000, thickness=200))
        structure.append(ColumnEntity(x_pos=2500, width=400, height=3000))
        structure.append(CeilingEntity(ceiling_height=2700, length=10000, width=3000))
        return structure

    def _build_pipe_system(self) -> List:
        """构建管道系统"""
        from models import (
            PipeEntity, SupportEntity, ValveEntity, ClampEntity,
            FlangeEntity, GasketEntity, BoltEntity, WheelEntity, StemEntity,
        )
        pipes = []

        # 1. 主管道（10米）
        pipe = PipeEntity(
            dn='DN100',
            start={'x': 0, 'y': -150, 'z': 2500},
            end={'x': 10000, 'y': -150, 'z': 2500},
        )
        pipes.append(pipe)

        # 2. 支架（5个）
        # ★ A-2 新增：每个支架创建 2 个锚点实体
        from models.anchor import AnchorEntity
        for i in range(5):
            support = SupportEntity(index=i, x_pos=1000 + i * 2000)
            pipes.append(support)

            # 从支架的 L2 里读取锚点定义，创建锚点实体
            support.anchors = []
            anchor_l2_list = support.layer['l2_static_attributes'].get('锚点', [])
            for anchor_info in anchor_l2_list:
                anchor_rel = anchor_info.get('位置', {'x': 0, 'y': 0, 'z': 0})
                anchor_abs = {
                    'x': support.x_pos + anchor_rel.get('x', 0),
                    'y': -100 + anchor_rel.get('y', 0),
                    'z': 2500 + anchor_rel.get('z', 0),
                }
                anchor = AnchorEntity(
                    anchor_type='M12_膨胀螺栓孔',
                    owner_id=support.id,
                    position=anchor_abs,
                )
                # 把锚点ID回写到支架的 L2 里
                anchor_info['实体ID'] = anchor.id
                support.anchors.append(anchor)

        # 3. 卡箍（1个，位于6米处）
        clamp = ClampEntity(dn='DN100', position={'x': 6000, 'y': -150, 'z': 2500})
        pipes.append(clamp)

        # 4. 阀门装配（55个零件）
        valve_parts = self._build_valve_assembly({
            'position': {'x': 4000, 'y': -150, 'z': 2500},
        })
        pipes.extend(valve_parts)

        return pipes

    def _build_valve_assembly(self, cfg: Dict) -> List:
        """构建阀门装配（55个零件）"""
        from models import (
            ValveEntity, WheelEntity, StemEntity,
            FlangeEntity, GasketEntity, BoltEntity,
        )
        parts = []
        pos = cfg.get('position', {'x': 4000, 'y': -150, 'z': 2500})

        # 1. 阀体（1个）
        valve = ValveEntity(valve_type='闸阀', dn='DN100', position=pos)
        parts.append(valve)

        # 2. 手轮（1个）
        wheel = WheelEntity(dn='DN100', position={'x': pos['x'], 'y': pos['y'], 'z': pos['z'] + 300},
                            connect_valve=valve.id)
        parts.append(wheel)

        # 3. 阀杆（1个）
        stem = StemEntity(dn='DN100', position={'x': pos['x'], 'y': pos['y'], 'z': pos['z'] + 200},
                          connect_valve=valve.id, connect_wheel=wheel.id)
        parts.append(stem)

        # 4. 法兰（2个）
        for i in range(2):
            flange = FlangeEntity(dn='DN100',
                                  position={'x': pos['x'] + (i * 280 - 140), 'y': pos['y'], 'z': pos['z']})
            parts.append(flange)

        # 5. 垫片（2个）
        for i in range(2):
            gasket = GasketEntity(dn='DN100',
                                  position={'x': pos['x'] + (i * 280 - 140), 'y': pos['y'], 'z': pos['z']})
            parts.append(gasket)

        # 6. 螺栓（16个）
        for i in range(16):
            bolt = BoltEntity(spec='M16', bolt_type='法兰螺栓',
                              position={'x': pos['x'], 'y': pos['y'], 'z': pos['z']})
            parts.append(bolt)

        # 7. 螺母（16个）
        for i in range(16):
            nut = BoltEntity(spec='M16', bolt_type='螺母',
                             position={'x': pos['x'], 'y': pos['y'], 'z': pos['z']})
            parts.append(nut)

        # 8. 垫圈（16个）
        for i in range(16):
            washer = BoltEntity(spec='M16', bolt_type='垫圈',
                                position={'x': pos['x'], 'y': pos['y'], 'z': pos['z']})
            parts.append(washer)

        return parts  # 1+1+1+2+2+16+16+16 = 55个

    def _build_other_disciplines(self) -> List:
        """构建风管/桥架"""
        from models import DuctEntity, TrayEntity
        return [
            DuctEntity(spec='800×400',
                       start={'x': 0, 'y': -600, 'z': 2800},
                       end={'x': 10000, 'y': -600, 'z': 2800}),
            TrayEntity(spec='300×200',
                       start={'x': 0, 'y': -1000, 'z': 2700},
                       end={'x': 10000, 'y': -1000, 'z': 2700}),
        ]

    def _build_drawings(self) -> List:
        """构建图纸"""
        from models import DrawingEntity
        return [
            DrawingEntity(drawing_name='消防管道平面图', discipline='消防',
                          drawing_type='平面图', version='v1.0', designer='王设计'),
        ]

    def _build_contract(self):
        """构建合同"""
        from models import ContractEntity
        return ContractEntity(
            contract_type='总包',
            party_a='甲方',
            party_b='施工单位',
            amount=500000,
            duration_days=120,
        )

    def _build_assembly_test_area(self) -> List:
        """构建装配测试区"""
        from models import FlangeEntity, BoltEntity
        parts = []
        # 目标：FLANGE-005
        flange = FlangeEntity(dn='DN100', position={'x': 5000, 'y': -800, 'z': 100})
        parts.append(flange)
        # M16螺栓（能装）
        bolt_m16 = BoltEntity(spec='M16', position={'x': 1000, 'y': -800, 'z': 100})
        parts.append(bolt_m16)
        # M20螺栓（装不上）
        bolt_m20 = BoltEntity(spec='M20', position={'x': 1200, 'y': -800, 'z': 100})
        parts.append(bolt_m20)
        return parts

    # ==================== 摘要 ====================

    def get_summary(self) -> Dict[str, Any]:
        """获取场景摘要"""
        by_type: Dict[str, int] = {}
        for e in self.entities:
            etype = getattr(e, 'entity_type', '未知')
            by_type[etype] = by_type.get(etype, 0) + 1
        return {
            'total': len(self.entities),
            'by_type': by_type,
        }


def build_full_scene() -> Dict[str, Any]:
    """快捷函数"""
    return SceneBuilder().build_full_scene()