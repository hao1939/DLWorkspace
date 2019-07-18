from job_deployer import JobDeployer


class JobRole:
    MARK_ROLE_READY_FILE = "/pod/running/ROLE_READY"

    @staticmethod
    def get_job_roles(job_id):
        deployer = JobDeployer()
        pods = deployer.get_pods(label_selector="run={}".format(job_id))

        job_roles = []
        for pod in pods:
            pod_name = pod.metadata.name
            if "distRole" in pod.metadata.labels:
                role = pod.metadata.labels["distRole"]
            else:
                role = "master"
            job_role = JobRole(role, pod_name)
            job_roles.append(job_role)
        return job_roles

    def __init__(self, role_name, pod_name):
        self.role_name = role_name
        self.pod_name = pod_name

    def status(self):
        """
        Return role status in ["NotFound", "Pending", "Running", "Succeeded", "Failed", "Unknown"]
        It's slightly different from pod phase, when pod is running:
            CONTAINER_READY -> WORKER_READY -> JOB_READY (then the job finally in "Running" status.)
        """
        # pod-phase: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-phase
        deployer = JobDeployer()
        pods = deployer.get_pods(field_selector="metadata.name={}".format(self.pod_name))
        if(len(pods) < 1):
            return "NotFound"

        assert(len(pods) == 1)
        pod = pods[0]
        phase = pod.status.phase

        # !!! Pod is runing, doesn't mean "Role" is ready and running.
        if(phase == "Running"):
            if not self.isRoleReady():
                return "Pending"

        return phase

    def isFileExisting(self, file):
        deployer = JobDeployer()
        status_code, _ = deployer.pod_exec(self.pod_name, ["/bin/sh", "-c", "ls -lrt {}".format(file)])
        return status_code == 0

    def isRoleReady(self):
        return self.isFileExisting(JobRole.MARK_ROLE_READY_FILE)