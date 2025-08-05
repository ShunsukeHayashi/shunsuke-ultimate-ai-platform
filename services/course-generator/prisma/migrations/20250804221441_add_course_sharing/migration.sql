-- CreateEnum
CREATE TYPE "public"."SharePermission" AS ENUM ('VIEW_ONLY', 'VIEW_AND_EXPORT', 'FULL_ACCESS');

-- CreateTable
CREATE TABLE "public"."CourseShare" (
    "id" TEXT NOT NULL,
    "courseId" TEXT NOT NULL,
    "shareToken" TEXT NOT NULL,
    "permission" "public"."SharePermission" NOT NULL DEFAULT 'VIEW_ONLY',
    "sharedWithEmail" TEXT,
    "sharedWithUserId" TEXT,
    "sharedBy" TEXT NOT NULL,
    "description" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "expiresAt" TIMESTAMP(3),
    "maxViews" INTEGER,
    "currentViews" INTEGER NOT NULL DEFAULT 0,
    "password" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "lastAccessedAt" TIMESTAMP(3),

    CONSTRAINT "CourseShare_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."ShareAccessLog" (
    "id" TEXT NOT NULL,
    "shareId" TEXT NOT NULL,
    "accessedBy" TEXT,
    "userAgent" TEXT,
    "action" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ShareAccessLog_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "CourseShare_shareToken_key" ON "public"."CourseShare"("shareToken");

-- CreateIndex
CREATE INDEX "CourseShare_courseId_idx" ON "public"."CourseShare"("courseId");

-- CreateIndex
CREATE INDEX "CourseShare_shareToken_idx" ON "public"."CourseShare"("shareToken");

-- CreateIndex
CREATE INDEX "CourseShare_sharedWithEmail_idx" ON "public"."CourseShare"("sharedWithEmail");

-- CreateIndex
CREATE INDEX "CourseShare_isActive_expiresAt_idx" ON "public"."CourseShare"("isActive", "expiresAt");

-- CreateIndex
CREATE INDEX "ShareAccessLog_shareId_idx" ON "public"."ShareAccessLog"("shareId");

-- CreateIndex
CREATE INDEX "ShareAccessLog_createdAt_idx" ON "public"."ShareAccessLog"("createdAt");

-- AddForeignKey
ALTER TABLE "public"."CourseShare" ADD CONSTRAINT "CourseShare_courseId_fkey" FOREIGN KEY ("courseId") REFERENCES "public"."Course"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."ShareAccessLog" ADD CONSTRAINT "ShareAccessLog_shareId_fkey" FOREIGN KEY ("shareId") REFERENCES "public"."CourseShare"("id") ON DELETE CASCADE ON UPDATE CASCADE;
